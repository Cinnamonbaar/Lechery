extends Node

var stage: int = 0
var timer: float = 0.0
var total_elapsed: float = 0.0
const MAX_TOTAL_TIMEOUT: float = 20.0

var char_node: CharacterController
var cam_node: OrbitCamera

func _ready() -> void:
	print("==================================================")
	print("--- LIVE VERIFICATION RUNNER STARTED ---")
	print("==================================================")
	
	char_node = get_node_or_null("../Character")
	cam_node = get_node_or_null("../OrbitCamera")
	
	if not char_node:
		_fail_exit("Character node not found!")
		return
	if not cam_node:
		_fail_exit("OrbitCamera node not found!")
		return

func _process(delta: float) -> void:
	total_elapsed += delta
	if total_elapsed > MAX_TOTAL_TIMEOUT:
		_fail_exit("Global safety timeout reached (" + str(MAX_TOTAL_TIMEOUT) + "s) - aborting!")
		return

	timer += delta
	match stage:
		0:
			# Creator Mode: Verify idle animation and equip Style 1 (Sleek Bob)
			if timer > 0.6:
				print("[STAGE 0] Checking Creator Mode & Idle Animation...")
				if not char_node.anim_player:
					_fail_exit("anim_player is null!")
					return
				
				var cur_anim = char_node.anim_player.current_animation
				print("  Current Animation: '", cur_anim, "'")
				if cur_anim != "locomotion/idle":
					_fail_exit("Expected 'locomotion/idle', got: " + cur_anim)
					return
				
				print("  Equipping Sleek Bob hair (Style 1)...")
				char_node.set_hair_style(1)
				if char_node.overlay_hair_data.is_empty():
					_fail_exit("No hair data loaded!")
					return
				
				var hair_root = char_node.overlay_hair_data[0].root
				if hair_root.get_parent() != char_node.head_bone_attachment:
					_fail_exit("Hair root is parented to " + str(hair_root.get_parent()) + ", expected head_bone_attachment")
					return
				print("  Hair correctly parented to head_bone_attachment!")
				
				# Focus on face for closeup screenshot
				cam_node.focus_face()
				cam_node.distance = 0.75
				cam_node._current_offset = Vector3(0.0, 1.35, 0.0)
				cam_node._yaw = 0.0
				cam_node._target_yaw = 0.0
				
				stage = 1
				timer = 0.0
		1:
			# Capture Style 1 and switch to Style 2
			if timer > 0.4:
				print("[STAGE 1] Capturing Style 1 (Sleek Bob)...")
				_capture_screen("verify_style_1_bob_face.png")
				print("  Equipping Cat-Ear Twin Pigtails (Style 2)...")
				char_node.set_hair_style(2)
				stage = 2
				timer = 0.0
		2:
			# Capture Style 2 and switch to Style 3
			if timer > 0.4:
				print("[STAGE 2] Capturing Style 2 (Cat-Ear Twin Pigtails)...")
				_capture_screen("verify_style_2_twintails_face.png")
				print("  Equipping Long Side Ponytail (Style 3)...")
				char_node.set_hair_style(3)
				stage = 3
				timer = 0.0
		3:
			# Capture Style 3 and switch back to Style 1 for locomotion tests
			if timer > 0.4:
				print("[STAGE 3] Capturing Style 3 (Long Side Ponytail)...")
				_capture_screen("verify_style_3_ponytail_face.png")
				print("  Resetting to Style 1 for locomotion & camera tests...")
				char_node.set_hair_style(1)
				cam_node.reset_view()
				cam_node.distance = 1.9
				cam_node._current_offset = Vector3(0.0, 1.05, 0.0)
				stage = 4
				timer = 0.0
		4:
			# 360 degree hair lock test
			if timer > 0.4:
				print("[STAGE 4] Testing 360 degree hair rotation tracking...")
				var hair_root = char_node.overlay_hair_data[0].root
				var skel = char_node.skeleton
				var h_bone = char_node.head_bone_idx
				var init_head = skel.global_transform * skel.get_bone_global_pose(h_bone).origin
				var init_hair = hair_root.global_position
				var init_dist = (init_hair - init_head).length()
				
				for deg in [30.0, 90.0, 180.0, 270.0, 360.0]:
					char_node.active_character_root.rotation.y = deg_to_rad(deg)
					char_node.active_character_root.force_update_transform()
					char_node.head_bone_attachment.force_update_transform()
					hair_root.force_update_transform()
					var cur_head = skel.global_transform * skel.get_bone_global_pose(h_bone).origin
					var cur_hair = hair_root.global_position
					var dist = (cur_hair - cur_head).length()
					var diff = abs(dist - init_dist)
					if diff > 0.01:
						_fail_exit("Hair detached during rotation at " + str(deg) + " deg! Drift: " + str(diff))
						return
				
				print("  360-degree rotation test passed: 0 hair drift relative to head!")
				
				# Reset rotation and transition to Walk Mode
				char_node.active_character_root.rotation.y = 0.0
				char_node.global_position = Vector3(0, 0.12, 0)
				char_node.set_controller_mode(CharacterController.ControllerMode.MODE_WALK)
				cam_node.set_camera_mode(OrbitCamera.CameraMode.MODE_WALK)
				print("  Switched to Walk Mode.")
				stage = 5
				timer = 0.0
		5:
			# Walk Mode Locomotion test
			# Walk forward (-Z) at 1.5 m/s within the pedestal
			char_node.velocity = Vector3(0, 0, -1.5)
			char_node.move_and_slide()
			
			if timer > 0.4:
				print("[STAGE 5] Checking 3rd-Person Locomotion Animation & Heading...")
				var cur_anim = char_node.anim_player.current_animation
				var heading = char_node.active_character_root.rotation.y
				print("  Current Animation: '", cur_anim, "'")
				print("  Model Heading (rad): ", heading, " (expected approx PI = ", PI, ")")
				
				if cur_anim != "locomotion/walk":
					_fail_exit("Expected 'locomotion/walk' while moving, got: " + cur_anim)
					return
				
				if abs(heading - PI) > 0.2 and abs(heading + PI) > 0.2:
					_fail_exit("Model heading incorrect while moving -Z! Got: " + str(heading))
					return
				
				print("  Locomotion walk animation and forward heading verified!")
				_capture_screen("verify_walk_3rd_person_locomotion.png")
				
				# Transition to True First Person & Reset position
				char_node.global_position = Vector3(0, 0.12, 0)
				char_node.velocity = Vector3.ZERO
				cam_node._target_distance = 0.0
				cam_node.distance = 0.0
				cam_node._target_pitch = 0.0
				cam_node._pitch = 0.0
				cam_node._target_yaw = 0.0
				cam_node._yaw = 0.0
				stage = 6
				timer = 0.0
		6:
			# First Person Orientation test
			char_node.velocity = Vector3(0, 0, -1.0)
			char_node.move_and_slide()
			
			if timer > 0.4:
				print("[STAGE 6] Checking First-Person View & Body Alignment...")
				if not cam_node.is_in_first_person():
					_fail_exit("Camera not detected in first person!")
					return
				
				if cam_node.cull_mask != 1:
					_fail_exit("Direct FP camera must cull Layer 2! cull_mask is: " + str(cam_node.cull_mask))
					return
				
				var body_heading = char_node.active_character_root.rotation.y
				print("  FP Body Heading: ", body_heading, " (expected PI)")
				if abs(body_heading - PI) > 0.1 and abs(body_heading + PI) > 0.1:
					_fail_exit("Body not facing camera forward in FP! Got: " + str(body_heading))
					return
				
				print("  First-person alignment and cull mask verified!")
				_capture_screen("verify_first_person_forward.png")
				
				# Look down at body/chest/feet
				cam_node._pitch = deg_to_rad(-55.0)
				cam_node._target_pitch = deg_to_rad(-55.0)
				stage = 7
				timer = 0.0
		7:
			# First Person Looking Down test
			if timer > 0.5:
				print("[STAGE 7] Checking First-Person Looking Down at Body...")
				_capture_screen("verify_first_person_look_down_body.png")
				print("==================================================")
				print("--- ALL LIVE VERIFICATIONS PASSED SUCCESSFULLY! ---")
				print("==================================================")
				stage = 8
				get_tree().quit(0)

func _fail_exit(err_msg: String) -> void:
	printerr("\n[VERIFICATION ERROR] ", err_msg)
	print("Verification failed! Exiting with code 1.")
	get_tree().quit(1)

func _capture_screen(filename: String) -> void:
	var img = get_viewport().get_texture().get_image()
	var path = ProjectSettings.globalize_path("user://" + filename)
	var err = img.save_png(path)
	if err == OK:
		print("  [Screenshot Saved] -> ", path)
	else:
		printerr("  Failed to save screenshot: ", err)

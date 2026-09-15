extends CharacterBody3D
class_name CharacterController

signal character_loaded
signal trait_changed(trait_name: String, new_value: Variant)
signal mode_changed(new_mode: int)

enum ControllerMode {
	MODE_CREATOR,
	MODE_WALK
}

const BASE_MODEL_PATH: String = "res://assets/models/main_humanoid_base_andro.glb"

const MODULAR_HAIR_DEFS: Array[Dictionary] = [
	{
		"name": "Style 0: Natural Bald (Base)",
		"type": "none"
	},
	{
		"name": "Style 1: Sleek Bob",
		"type": "overlay",
		"path": "res://assets/models/Sendagaya_Shino.glb",
		"offset": Vector3(0.0, -0.010, -0.014),
		"scale": Vector3(1.02, 1.01, 1.03)
	},
	{
		"name": "Style 2: Cat-Ear Twin Pigtails",
		"type": "overlay",
		"path": "res://assets/models/HairSample_Female.glb",
		"offset": Vector3(0.0, -0.022, -0.018),
		"scale": Vector3(1.03, 1.02, 1.04)
	},
	{
		"name": "Style 3: Long Side Ponytail",
		"type": "overlay",
		"path": "res://assets/models/Victoria_Rubin.glb",
		"offset": Vector3(0.0, -0.005, -0.004),
		"scale": Vector3(1.01, 1.00, 1.01)
	}
]

const EYE_SHADER: Shader = preload("res://shaders/anime_eye_color.gdshader")
const HAIR_SHADER: Shader = preload("res://shaders/anime_hair_color.gdshader")

# Movement constants
const WALK_SPEED: float = 2.8
const SPRINT_SPEED: float = 5.5
const JUMP_VELOCITY: float = 4.5
const GRAVITY: float = 12.0
const ROTATION_ACCEL: float = 12.0

@export var camera_ref: Camera3D

var current_mode: int = ControllerMode.MODE_CREATOR

var active_character_root: Node3D
var skeleton: Skeleton3D
var head_bone_attachment: BoneAttachment3D
var face_mesh_instance: MeshInstance3D
var body_mesh_instance: MeshInstance3D

var head_bone_idx: int = 12
var bust_bone_indices: Array[int] = []
var shoulder_bone_indices: Array[int] = []
var hip_bone_idx: int = -1

# Locomotion bone indices
var left_upper_leg_idx: int = -1
var right_upper_leg_idx: int = -1
var left_lower_leg_idx: int = -1
var right_lower_leg_idx: int = -1
var left_upper_arm_idx: int = -1
var right_upper_arm_idx: int = -1

var eye_material: ShaderMaterial
var skin_materials: Array[StandardMaterial3D] = []
var hair_materials: Array[ShaderMaterial] = []
var overlay_hair_data: Array[Dictionary] = []

var current_hair_style_idx: int = 0
var hair_depth_bias: float = 0.0
var hair_height_bias: float = 0.0

# Current customization / transformation state
var femininity: float = 0.5 # 0.0 = Masc, 0.5 = Andro, 1.0 = Fem
var breast_scale: float = 0.5 # 0.0 = Flat/Pecs, 1.0 = Moderate, 2.5 = Voluptuous
var shoulder_scale: float = 1.0
var hip_scale: float = 1.0
var current_height: float = 1.0
var current_eye_color: Color = Color(0.18, 0.45, 0.85)
var current_eye_brightness: float = 1.0
var current_eye_saturation: float = 1.0
var current_hair_color: Color = Color(1.0, 1.0, 1.0)
var current_hair_brightness: float = 1.0
var current_hair_saturation: float = 1.0
var current_skin_color: Color = Color(1.0, 1.0, 1.0)

const ANIM_PATHS: Dictionary = {
	"idle": "res://assets/animations/locomotion/idle.fbx",
	"walk": "res://assets/animations/locomotion/walk.fbx",
	"run": "res://assets/animations/locomotion/run.fbx",
	"sprint": "res://assets/animations/locomotion/sprint.fbx",
	"jump_begin": "res://assets/animations/locomotion/jump_begin.fbx",
	"jump_fall": "res://assets/animations/locomotion/jump_fall.fbx",
	"jump_land": "res://assets/animations/locomotion/jump_land.fbx"
}

var anim_player: AnimationPlayer
var current_anim_state: String = ""
var _was_in_air: bool = false
var _target_heading: float = 0.0

func _ready() -> void:
	load_base_character()

func _process(_delta: float) -> void:
	pass

func _physics_process(delta: float) -> void:
	if current_mode == ControllerMode.MODE_WALK:
		_process_walk_physics(delta)
	else:
		# Creator mode: ensure stationary and play breathing idle
		velocity = Vector3.ZERO
		_play_locomotion("idle", 0.3)
		if anim_player:
			anim_player.speed_scale = 1.0

func _process_walk_physics(delta: float) -> void:
	# 1. Gravity
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	else:
		if velocity.y < 0.0:
			velocity.y = 0.0

	# 2. Jump
	if is_on_floor() and (Input.is_key_pressed(KEY_SPACE) or Input.is_action_just_pressed("ui_accept")):
		velocity.y = JUMP_VELOCITY

	# 3. WASD Movement Input
	var input_vec: Vector2 = Vector2.ZERO
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		input_vec.y += 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		input_vec.y -= 1.0
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		input_vec.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		input_vec.x += 1.0

	var is_sprinting: bool = Input.is_key_pressed(KEY_SHIFT)
	var move_speed: float = SPRINT_SPEED if is_sprinting else WALK_SPEED

	var move_dir: Vector3 = Vector3.ZERO
	var cam_yaw: float = 0.0
	if camera_ref:
		cam_yaw = camera_ref.rotation.y

	if input_vec.length_squared() > 0.001:
		input_vec = input_vec.normalized()
		# Relative to camera orientation:
		var forward: Vector3 = -Vector3(sin(cam_yaw), 0.0, cos(cam_yaw))
		var right: Vector3 = Vector3(cos(cam_yaw), 0.0, -sin(cam_yaw))
		move_dir = (forward * input_vec.y + right * input_vec.x).normalized()

	# 4. Apply horizontal velocity
	var target_vel: Vector3 = move_dir * move_speed
	velocity.x = lerp(velocity.x, target_vel.x, delta * 12.0)
	velocity.z = lerp(velocity.z, target_vel.z, delta * 12.0)

	move_and_slide()

	# 5. Model Orientation
	var horiz_vel: Vector2 = Vector2(velocity.x, velocity.z)
	var horiz_speed: float = horiz_vel.length()
	
	if active_character_root:
		# Check if in first person:
		var in_fp: bool = false
		if camera_ref and camera_ref.has_method("is_in_first_person"):
			in_fp = camera_ref.is_in_first_person()
			
		if in_fp:
			# Lock heading directly to camera forward heading in first-person (model faces -Z at yaw=0, so +PI)
			active_character_root.rotation.y = cam_yaw + PI
		elif horiz_speed > 0.2:
			# Smoothly face movement heading in 3rd person
			_target_heading = atan2(velocity.x, velocity.z)
			active_character_root.rotation.y = lerp_angle(active_character_root.rotation.y, _target_heading, delta * ROTATION_ACCEL)

	# 6. Real Humanoid Locomotion Animation
	var is_on_ground: bool = is_on_floor()
	if not is_on_ground:
		_was_in_air = true
		if velocity.y > 0.5:
			_play_locomotion("jump_begin", 0.15)
		else:
			_play_locomotion("jump_fall", 0.2)
		if anim_player:
			anim_player.speed_scale = 1.0
	else:
		if _was_in_air:
			_was_in_air = false
			_play_locomotion("jump_land", 0.1)
			if anim_player:
				anim_player.speed_scale = 1.0
		else:
			if horiz_speed < 0.2:
				_play_locomotion("idle", 0.3)
				if anim_player:
					anim_player.speed_scale = 1.0
			elif is_sprinting:
				_play_locomotion("sprint", 0.2)
				if anim_player:
					anim_player.speed_scale = clamp(horiz_speed / 4.8, 0.8, 1.4)
			elif horiz_speed > 3.0:
				_play_locomotion("run", 0.2)
				if anim_player:
					anim_player.speed_scale = clamp(horiz_speed / 3.6, 0.8, 1.3)
			else:
				_play_locomotion("walk", 0.2)
				if anim_player:
					anim_player.speed_scale = clamp(horiz_speed / 2.2, 0.7, 1.4)

func _play_locomotion(anim_name: String, blend_time: float = 0.2) -> void:
	if current_anim_state == anim_name and anim_player and anim_player.is_playing():
		return
	current_anim_state = anim_name
	var full_name: String = "locomotion/" + anim_name
	if anim_player and anim_player.has_animation(full_name):
		anim_player.play(full_name, blend_time)

## Mode Switcher (Creator vs Walk Mode)
func set_controller_mode(new_mode: int) -> void:
	current_mode = new_mode
	if current_mode == ControllerMode.MODE_CREATOR:
		velocity = Vector3.ZERO
		_was_in_air = false
		if active_character_root:
			active_character_root.rotation.y = 0.0 # Face the front creator camera
		_play_locomotion("idle", 0.3)
		if anim_player:
			anim_player.speed_scale = 1.0
	else:
		# Enter Walk Mode: start facing forward into dungeon room
		if active_character_root:
			active_character_root.rotation.y = PI
			_target_heading = PI
	emit_signal("mode_changed", current_mode)

## Loads the base character and mounts modular hairstyles
func load_base_character() -> void:
	# Only clean up dynamically generated avatar root and hair roots
	if active_character_root and is_instance_valid(active_character_root):
		active_character_root.queue_free()
	for data in overlay_hair_data:
		if is_instance_valid(data.root):
			data.root.queue_free()
	
	overlay_hair_data.clear()
	hair_materials.clear()
	skin_materials.clear()
	bust_bone_indices.clear()
	shoulder_bone_indices.clear()
	hip_bone_idx = -1
	skeleton = null
	head_bone_attachment = null
	face_mesh_instance = null
	body_mesh_instance = null
	eye_material = null
	
	var gltf: GLTFDocument = GLTFDocument.new()
	var state: GLTFState = GLTFState.new()
	var err: Error = gltf.append_from_file(BASE_MODEL_PATH, state)
	if err != OK:
		push_error("Failed to load base model: " + BASE_MODEL_PATH)
		return
	active_character_root = gltf.generate_scene(state) as Node3D
	if not active_character_root:
		push_error("Failed to generate scene from base model.")
		return
		
	add_child(active_character_root)
	_map_base_nodes(active_character_root)
	
	# Mount modular hairstyles with intact skeletons and calibrated head fitting
	_mount_modular_hairstyles()
	
	# Setup retargeted locomotion animation library (idle, walk, run, sprint, jump)
	_setup_animation_library()
	_play_locomotion("idle", 0.0)
	
	# Apply initial transformation values
	set_shoulder_width(shoulder_scale)
	set_height_scale(current_height)
	set_hair_style(0)
	
	emit_signal("character_loaded")

func _map_base_nodes(root: Node) -> void:
	skeleton = _find_skeleton(root)
	if skeleton:
		skeleton.unique_name_in_owner = true
		head_bone_idx = skeleton.find_bone("Head")
		if head_bone_idx < 0:
			head_bone_idx = skeleton.find_bone("J_Bip_C_Head")
			
		if head_bone_idx >= 0:
			head_bone_attachment = BoneAttachment3D.new()
			head_bone_attachment.name = "HeadBoneAttachment"
			head_bone_attachment.bone_name = skeleton.get_bone_name(head_bone_idx)
			skeleton.add_child(head_bone_attachment)
			
		hip_bone_idx = skeleton.find_bone("Hips")
		if hip_bone_idx < 0:
			hip_bone_idx = skeleton.find_bone("J_Bip_C_Hips")
			
		left_upper_leg_idx = skeleton.find_bone("LeftUpperLeg")
		if left_upper_leg_idx < 0:
			left_upper_leg_idx = skeleton.find_bone("J_Bip_L_UpperLeg")
			
		right_upper_leg_idx = skeleton.find_bone("RightUpperLeg")
		if right_upper_leg_idx < 0:
			right_upper_leg_idx = skeleton.find_bone("J_Bip_R_UpperLeg")
			
		left_lower_leg_idx = skeleton.find_bone("LeftLowerLeg")
		if left_lower_leg_idx < 0:
			left_lower_leg_idx = skeleton.find_bone("J_Bip_L_LowerLeg")
			
		right_lower_leg_idx = skeleton.find_bone("RightLowerLeg")
		if right_lower_leg_idx < 0:
			right_lower_leg_idx = skeleton.find_bone("J_Bip_R_LowerLeg")
			
		left_upper_arm_idx = skeleton.find_bone("LeftUpperArm")
		if left_upper_arm_idx < 0:
			left_upper_arm_idx = skeleton.find_bone("J_Bip_L_UpperArm")
			
		right_upper_arm_idx = skeleton.find_bone("RightUpperArm")
		if right_upper_arm_idx < 0:
			right_upper_arm_idx = skeleton.find_bone("J_Bip_R_UpperArm")

		for i in range(skeleton.get_bone_count()):
			var bname: String = skeleton.get_bone_name(i).to_lower()
			if "bust" in bname:
				bust_bone_indices.append(i)
			elif "shoulder" in bname:
				shoulder_bone_indices.append(i)
	
	var meshes: Array[MeshInstance3D] = []
	_collect_meshes(root, meshes)
	
	for m in meshes:
		var mname: String = m.name.to_lower()
		if "face" in mname:
			face_mesh_instance = m
			# Visual Layer 2: Player Head (excluded only from 1st-person eyes, visible in mirrors & 3rd-person)
			m.layers = 2
			_setup_mesh_materials(m)
		elif "body" in mname:
			body_mesh_instance = m
			# Visual Layer 1: General World & Player Body (visible when looking down in 1st-person!)
			m.layers = 1
			_setup_mesh_materials(m)

func _mount_modular_hairstyles() -> void:
	for def in MODULAR_HAIR_DEFS:
		if def.type != "overlay":
			continue
			
		var path: String = def.path
		if not FileAccess.file_exists(path):
			continue
			
		var gltf: GLTFDocument = GLTFDocument.new()
		var state: GLTFState = GLTFState.new()
		if gltf.append_from_file(path, state) != OK:
			continue
			
		var hair_scene: Node3D = gltf.generate_scene(state) as Node3D
		if not hair_scene:
			continue
			
		# Hide face, body, clothes, accessories - KEEP ONLY HAIR
		for m in hair_scene.find_children("*", "MeshInstance3D"):
			if not ("hair" in m.name.to_lower()):
				m.visible = false
			else:
				# Hair is on Visual Layer 2 (Player Head)
				m.layers = 2
				_collect_hair_materials(m)
				
		var skel: Skeleton3D = _find_skeleton(hair_scene)
		var h_idx: int = skel.find_bone("J_Bip_C_Head") if skel else -1
		
		# Calibrated Head Alignment using BoneAttachment3D
		if skel and h_idx >= 0 and head_bone_attachment:
			var hair_head_rest: Vector3 = skel.get_bone_global_rest(h_idx).origin
			hair_scene.rotation.y = PI
			var rotated_hair_head: Vector3 = hair_scene.basis * hair_head_rest
			var calib_offset: Vector3 = def.get("offset", Vector3.ZERO)
			var calib_scale: Vector3 = def.get("scale", Vector3.ONE)
			
			hair_scene.position = -rotated_hair_head + calib_offset
			hair_scene.scale = calib_scale
			hair_scene.visible = false
			head_bone_attachment.add_child(hair_scene)
		else:
			hair_scene.position = Vector3.ZERO
			hair_scene.rotation.y = 0.0
			hair_scene.visible = false
			if active_character_root:
				active_character_root.add_child(hair_scene)
			else:
				add_child(hair_scene)
		
		overlay_hair_data.append({
			"root": hair_scene,
			"skel": skel,
			"head_idx": h_idx,
			"def": def,
			"rest_transform": hair_scene.transform
		})

func _setup_animation_library() -> void:
	if not active_character_root or not skeleton:
		return
	anim_player = active_character_root.find_child("AnimationPlayer") as AnimationPlayer
	if not anim_player:
		anim_player = AnimationPlayer.new()
		anim_player.name = "AnimationPlayer"
		active_character_root.add_child(anim_player)

	var skel_rel_path: String = String(active_character_root.get_path_to(skeleton))
		
	var lib: AnimationLibrary = AnimationLibrary.new()
	for key in ANIM_PATHS.keys():
		var path: String = ANIM_PATHS[key]
		if not FileAccess.file_exists(path):
			continue
		var scene: PackedScene = load(path)
		if not scene:
			continue
		var inst: Node3D = scene.instantiate()
		var src_ap: AnimationPlayer = inst.find_child("AnimationPlayer")
		if src_ap and src_ap.get_animation_list().size() > 0:
			var src_anim_name: String = src_ap.get_animation_list()[0]
			var anim: Animation = src_ap.get_animation(src_anim_name).duplicate()
			
			# Map tracks to character skeleton and drop unmapped/extraneous tracks
			var t: int = anim.get_track_count() - 1
			while t >= 0:
				var p: String = String(anim.track_get_path(t))
				var colon_idx: int = p.find(":")
				if colon_idx >= 0:
					var bname: String = p.substr(colon_idx + 1)
					if skeleton.find_bone(bname) >= 0:
						anim.track_set_path(t, NodePath(skel_rel_path + ":" + bname))
					else:
						anim.remove_track(t)
				t -= 1
				
			if key in ["idle", "walk", "run", "sprint", "jump_fall"]:
				anim.loop_mode = Animation.LOOP_LINEAR
			else:
				anim.loop_mode = Animation.LOOP_NONE
			lib.add_animation(key, anim)
		inst.queue_free()
		
	if anim_player.has_animation_library("locomotion"):
		anim_player.remove_animation_library("locomotion")
	anim_player.add_animation_library("locomotion", lib)

func _apply_relaxed_pose() -> void:
	if not skeleton:
		return
	for i in range(skeleton.get_bone_count()):
		var bname: String = skeleton.get_bone_name(i)
		if bname == "J_Bip_L_UpperArm":
			var rot: Quaternion = Quaternion(Vector3(0, 0, 1), deg_to_rad(-65.0)) * Quaternion(Vector3(0, 1, 0), deg_to_rad(10.0))
			skeleton.set_bone_pose_rotation(i, rot)
		elif bname == "J_Bip_R_UpperArm":
			var rot: Quaternion = Quaternion(Vector3(0, 0, 1), deg_to_rad(65.0)) * Quaternion(Vector3(0, 1, 0), deg_to_rad(-10.0))
			skeleton.set_bone_pose_rotation(i, rot)
		elif bname in ["J_Bip_L_UpperLeg", "J_Bip_R_UpperLeg", "J_Bip_L_LowerLeg", "J_Bip_R_LowerLeg"]:
			skeleton.set_bone_pose_rotation(i, Quaternion.IDENTITY)

func _setup_mesh_materials(mesh_inst: MeshInstance3D) -> void:
	if not mesh_inst or not is_instance_valid(mesh_inst.mesh):
		return
	var mesh: Mesh = mesh_inst.mesh
	for s_idx in range(mesh.get_surface_count()):
		var mat: Material = mesh.surface_get_material(s_idx)
		if mat:
			var mat_name: String = mat.resource_name.to_lower()
			if "iris" in mat_name:
				var s_mat: ShaderMaterial = ShaderMaterial.new()
				s_mat.shader = EYE_SHADER
				if mat is StandardMaterial3D and mat.albedo_texture:
					s_mat.set_shader_parameter("albedo_texture", mat.albedo_texture)
				s_mat.set_shader_parameter("eye_tint", current_eye_color)
				s_mat.set_shader_parameter("brightness", current_eye_brightness)
				s_mat.set_shader_parameter("saturation", current_eye_saturation)
				mesh_inst.set_surface_override_material(s_idx, s_mat)
				eye_material = s_mat
			elif "skin" in mat_name:
				var dup_mat: StandardMaterial3D = mat.duplicate() as StandardMaterial3D
				if dup_mat:
					mesh_inst.set_surface_override_material(s_idx, dup_mat)
					skin_materials.append(dup_mat)
			else:
				var dup_mat: StandardMaterial3D = mat.duplicate() as StandardMaterial3D
				if dup_mat:
					mesh_inst.set_surface_override_material(s_idx, dup_mat)

func _collect_hair_materials(mesh_inst: MeshInstance3D) -> void:
	if not mesh_inst or not is_instance_valid(mesh_inst.mesh):
		return
	var mesh: Mesh = mesh_inst.mesh
	for s_idx in range(mesh.get_surface_count()):
		var mat: Material = mesh.surface_get_material(s_idx)
		if mat:
			var s_mat: ShaderMaterial = ShaderMaterial.new()
			s_mat.shader = HAIR_SHADER
			if mat is StandardMaterial3D:
				if mat.albedo_texture:
					s_mat.set_shader_parameter("albedo_texture", mat.albedo_texture)
				s_mat.set_shader_parameter("orig_color", mat.albedo_color)
			s_mat.set_shader_parameter("hair_color", current_hair_color)
			s_mat.set_shader_parameter("brightness", current_hair_brightness)
			s_mat.set_shader_parameter("saturation", current_hair_saturation)
			mesh_inst.set_surface_override_material(s_idx, s_mat)
			hair_materials.append(s_mat)

func _find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var s: Skeleton3D = _find_skeleton(child)
		if s:
			return s
	return null

func _collect_meshes(node: Node, list: Array[MeshInstance3D]) -> void:
	if node is MeshInstance3D:
		list.append(node)
	for child in node.get_children():
		_collect_meshes(child, list)

# ----------------- Transformation & Mutation API -----------------

## Master Genderbending Blend (0.0 = Full Masculine, 0.5 = Androgynous, 1.0 = Full Feminine)
func set_gender_blend(val: float) -> void:
	femininity = clamp(val, 0.0, 1.0)
	var target_bust: float = lerp(0.0, 2.0, femininity)
	var target_shoulder: float = lerp(1.22, 0.88, femininity)
	var target_hip: float = lerp(0.85, 1.25, femininity)
	
	set_breast_scale(target_bust)
	set_shoulder_width(target_shoulder)
	set_hip_width(target_hip)
	emit_signal("trait_changed", "femininity", femininity)

## Scale breasts dynamically via bust bones
func set_breast_scale(factor: float) -> void:
	breast_scale = clamp(factor, 0.0, 3.5)
	if skeleton and bust_bone_indices.size() > 0:
		for b_idx in bust_bone_indices:
			skeleton.set_bone_pose_scale(b_idx, Vector3(breast_scale, breast_scale, breast_scale))
	emit_signal("trait_changed", "breast_scale", breast_scale)

## Scale shoulder width
func set_shoulder_width(factor: float) -> void:
	shoulder_scale = clamp(factor, 0.7, 1.4)
	if skeleton and shoulder_bone_indices.size() > 0:
		for b_idx in shoulder_bone_indices:
			skeleton.set_bone_pose_scale(b_idx, Vector3(shoulder_scale, 1.0, 1.0))
	emit_signal("trait_changed", "shoulder_scale", shoulder_scale)

## Scale hip and pelvis width
func set_hip_width(factor: float) -> void:
	hip_scale = clamp(factor, 0.7, 1.5)
	if skeleton and hip_bone_idx >= 0:
		skeleton.set_bone_pose_scale(hip_bone_idx, Vector3(hip_scale, 1.0, hip_scale))
	emit_signal("trait_changed", "hip_scale", hip_scale)

## Scale total character height
func set_height_scale(factor: float) -> void:
	current_height = clamp(factor, 0.7, 1.4)
	scale = Vector3(current_height, current_height, current_height)
	emit_signal("trait_changed", "height_scale", current_height)

## Dynamically tint eye iris color
func set_eye_color(color: Color) -> void:
	current_eye_color = color
	if eye_material:
		eye_material.set_shader_parameter("eye_tint", color)
	emit_signal("trait_changed", "eye_color", color)

## Dynamically adjust eye brightness / lightness
func set_eye_brightness(val: float) -> void:
	current_eye_brightness = clamp(val, 0.2, 3.0)
	if eye_material:
		eye_material.set_shader_parameter("brightness", current_eye_brightness)
	emit_signal("trait_changed", "eye_brightness", current_eye_brightness)

## Dynamically adjust eye saturation
func set_eye_saturation(val: float) -> void:
	current_eye_saturation = clamp(val, 0.0, 2.5)
	if eye_material:
		eye_material.set_shader_parameter("saturation", current_eye_saturation)
	emit_signal("trait_changed", "eye_saturation", current_eye_saturation)

## Dynamically tint all skin materials (face + body unified)
func set_skin_color(color: Color) -> void:
	current_skin_color = color
	for mat in skin_materials:
		if is_instance_valid(mat):
			mat.albedo_color = color
	emit_signal("trait_changed", "skin_color", color)

## Switch active hairstyle
func set_hair_style(style_idx: int) -> void:
	current_hair_style_idx = style_idx
	var overlay_idx: int = 0
	for data in overlay_hair_data:
		data.root.visible = (style_idx == (overlay_idx + 1))
		overlay_idx += 1
		
	emit_signal("trait_changed", "hair_style", style_idx)

## Real-time micro hair fitting offsets
func set_hair_fitting(depth: float, height: float) -> void:
	hair_depth_bias = depth
	hair_height_bias = height
	_apply_hair_offsets()

func _apply_hair_offsets() -> void:
	for data in overlay_hair_data:
		var def = data.def
		var skel = data.skel
		var h_idx = data.head_idx
		if skel and h_idx >= 0 and head_bone_attachment:
			var hair_head_rest: Vector3 = skel.get_bone_global_rest(h_idx).origin
			var rotated_hair_head: Vector3 = data.root.basis * hair_head_rest
			var calib_offset: Vector3 = def.get("offset", Vector3.ZERO)
			var manual_offset: Vector3 = Vector3(0.0, hair_height_bias, hair_depth_bias)
			data.root.position = -rotated_hair_head + calib_offset + manual_offset

## Dynamically tint hair color across all mounted hairstyles
func set_hair_color(color: Color) -> void:
	current_hair_color = color
	for mat in hair_materials:
		if is_instance_valid(mat):
			mat.set_shader_parameter("hair_color", color)
	emit_signal("trait_changed", "hair_color", color)

## Dynamically adjust hair brightness / lightness
func set_hair_brightness(val: float) -> void:
	current_hair_brightness = clamp(val, 0.2, 3.0)
	for mat in hair_materials:
		if is_instance_valid(mat):
			mat.set_shader_parameter("brightness", current_hair_brightness)
	emit_signal("trait_changed", "hair_brightness", current_hair_brightness)

## Dynamically adjust hair saturation
func set_hair_saturation(val: float) -> void:
	current_hair_saturation = clamp(val, 0.0, 2.5)
	for mat in hair_materials:
		if is_instance_valid(mat):
			mat.set_shader_parameter("saturation", current_hair_saturation)
	emit_signal("trait_changed", "hair_saturation", current_hair_saturation)

## Returns global world position of the character's animated neck bone
func get_neck_global_position() -> Vector3:
	if skeleton:
		var n_idx: int = skeleton.find_bone("J_Bip_C_Neck")
		if n_idx >= 0:
			return (skeleton.global_transform * skeleton.get_bone_global_pose(n_idx)).origin
	return global_position + Vector3(0.0, 1.34, 0.0)

## Returns global world position of the character's animated head bone
func get_head_global_position() -> Vector3:
	if skeleton and head_bone_idx >= 0:
		return (skeleton.global_transform * skeleton.get_bone_global_pose(head_bone_idx)).origin
	return global_position + Vector3(0.0, 1.48, 0.0)

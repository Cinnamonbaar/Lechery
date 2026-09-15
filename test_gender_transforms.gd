extends SceneTree

func _init():
	var scene = load("res://scenes/test_room.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(12):
		await process_frame
		
	var character = scene.get_node("Character")
	var cam = scene.get_node("OrbitCamera")
	cam.focus_torso()
	
	# Test 1: Full Feminine Transformation
	character.set_gender_blend(1.0)
	character.set_hair_style(2) # Cat-ear twin pigtails
	character.set_hair_color(Color(0.98, 0.65, 0.78)) # Sakura pink
	character.set_eye_color(Color(0.95, 0.15, 0.25))  # Ruby eyes
	for i in range(20):
		await process_frame
	var img_fem = root.get_texture().get_image()
	if img_fem:
		img_fem.save_png("res://screenshot_transformed_fem.png")
		print("Feminine transformation captured!")
		
	# Test 2: Full Masculine Transformation
	character.set_gender_blend(0.0)
	character.set_hair_style(1) # Sleek bob
	character.set_hair_color(Color(0.2, 0.2, 0.25))   # Raven black
	character.set_eye_color(Color(0.15, 0.45, 0.95))  # Sapphire eyes
	for i in range(20):
		await process_frame
	var img_masc = root.get_texture().get_image()
	if img_masc:
		img_masc.save_png("res://screenshot_transformed_masc.png")
		print("Masculine transformation captured!")
		
	quit(0)

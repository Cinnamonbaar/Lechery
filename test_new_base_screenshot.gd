extends SceneTree

func _init():
	var scene = load("res://scenes/test_room.tscn").instantiate()
	root.add_child(scene)
	
	for i in range(15):
		await process_frame
		
	var img = root.get_texture().get_image()
	if img:
		img.save_png("res://screenshot_new_base.png")
		print("Saved screenshot_new_base.png successfully!")
	quit(0)

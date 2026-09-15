extends Control

const CharacterControllerScript = preload("res://scripts/character_controller.gd")
const OrbitCameraScript = preload("res://scripts/orbit_camera.gd")

@export var character: Node3D
@export var orbit_camera: Camera3D

# Panels & HUD
@onready var main_panel: PanelContainer = %MainPanel
@onready var bottom_dock: PanelContainer = %BottomDock
@onready var instruction_label: Label = %InstructionLabel
@onready var walk_mode_hud: PanelContainer = %WalkModeHUD
@onready var test_walk_btn: Button = %TestWalkBtn
@onready var exit_walk_btn: Button = %ExitWalkBtn

# Tab Navigation Buttons
@onready var body_tab_btn: Button = %BodyTabBtn
@onready var skin_tab_btn: Button = %SkinTabBtn
@onready var eyes_tab_btn: Button = %EyesTabBtn
@onready var hair_tab_btn: Button = %HairTabBtn

# Pages
@onready var body_page: Control = %BodyPage
@onready var skin_page: Control = %SkinPage
@onready var eyes_page: Control = %EyesPage
@onready var hair_page: Control = %HairPage

# Sliders & Value Labels - Body
@onready var shoulder_slider: HSlider = %ShoulderSlider
@onready var shoulder_label: Label = %ShoulderLabel
@onready var height_slider: HSlider = %HeightSlider
@onready var height_label: Label = %HeightLabel

# Sliders & Value Labels - Eyes
@onready var eye_brightness_slider: HSlider = %EyeBrightnessSlider
@onready var eye_brightness_label: Label = %EyeBrightnessLabel
@onready var eye_saturation_slider: HSlider = %EyeSaturationSlider
@onready var eye_saturation_label: Label = %EyeSaturationLabel

# Sliders & Value Labels - Hair
@onready var hair_brightness_slider: HSlider = %HairBrightnessSlider
@onready var hair_brightness_label: Label = %HairBrightnessLabel
@onready var hair_saturation_slider: HSlider = %HairSaturationSlider
@onready var hair_saturation_label: Label = %HairSaturationLabel
@onready var hair_depth_slider: HSlider = %HairDepthSlider
@onready var hair_depth_label: Label = %HairDepthLabel
@onready var hair_height_slider: HSlider = %HairHeightSlider
@onready var hair_height_label: Label = %HairHeightLabel

# Containers
@onready var skin_colors_container: HFlowContainer = %SkinColorsContainer
@onready var eye_colors_container: HFlowContainer = %EyeColorsContainer
@onready var hair_colors_container: HFlowContainer = %HairColorsContainer
@onready var hair_buttons_container: VBoxContainer = %HairButtonsContainer
@onready var hair_style_option: OptionButton = %HairStyleOption

@onready var turntable_check: CheckBox = %TurntableCheck

# Active swatch trackers
var active_skin_name: String = "Fair"
var active_eye_name: String = "Sapphire"
var active_hair_color_name: String = "Default"
var active_hair_style_idx: int = 0

var skin_swatch_buttons: Dictionary = {}
var eye_swatch_buttons: Dictionary = {}
var hair_swatch_buttons: Dictionary = {}
var hair_style_buttons: Array[Button] = []

# Palette definitions
const SKIN_PRESETS = {
	"Fair": Color(1.0, 1.0, 1.0),
	"Warm": Color(0.96, 0.88, 0.80),
	"Tanned": Color(0.85, 0.70, 0.56),
	"Ebony": Color(0.55, 0.40, 0.32),
	"Pale": Color(0.90, 0.92, 0.98),
	"Lilac": Color(0.92, 0.82, 0.95),
	"Orc": Color(0.72, 0.84, 0.68)
}

const EYE_PRESETS = {
	"Sapphire": Color(0.15, 0.45, 0.95),
	"Emerald": Color(0.15, 0.85, 0.35),
	"Ruby": Color(0.95, 0.15, 0.25),
	"Amber": Color(0.98, 0.75, 0.15),
	"Amethyst": Color(0.72, 0.2, 0.88),
	"Silver": Color(0.85, 0.9, 1.0)
}

const HAIR_PRESETS = {
	"Default": Color(1.0, 1.0, 1.0),
	"Raven": Color(0.18, 0.18, 0.22),
	"Blonde": Color(0.98, 0.85, 0.45),
	"Crimson": Color(0.85, 0.15, 0.25),
	"Sakura": Color(0.98, 0.65, 0.78),
	"Azure": Color(0.3, 0.65, 0.98)
}

func _ready() -> void:
	await get_tree().process_frame
	_setup_tabs()
	_setup_signals()
	_create_skin_swatches()
	_create_eye_swatches()
	_create_hair_style_buttons()
	_create_hair_color_swatches()
	_select_tab(0) # Default to Body
	_update_labels()

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB or event.keycode == KEY_ESCAPE:
			_toggle_walk_mode()
			get_viewport().set_input_as_handled()

func _toggle_walk_mode() -> void:
	if walk_mode_hud and walk_mode_hud.visible:
		_exit_walk_mode()
	else:
		_enter_walk_mode()

func _enter_walk_mode() -> void:
	if main_panel:
		main_panel.visible = false
	if bottom_dock:
		bottom_dock.visible = false
	if instruction_label:
		instruction_label.visible = false
	if walk_mode_hud:
		walk_mode_hud.visible = true

	if character and character.has_method("set_controller_mode"):
		character.set_controller_mode(CharacterControllerScript.ControllerMode.MODE_WALK)
	if orbit_camera and orbit_camera.has_method("set_camera_mode"):
		orbit_camera.set_camera_mode(OrbitCameraScript.CameraMode.MODE_WALK)

func _exit_walk_mode() -> void:
	if main_panel:
		main_panel.visible = true
	if bottom_dock:
		bottom_dock.visible = true
	if instruction_label:
		instruction_label.visible = true
	if walk_mode_hud:
		walk_mode_hud.visible = false

	if character and character.has_method("set_controller_mode"):
		character.set_controller_mode(CharacterControllerScript.ControllerMode.MODE_CREATOR)
	if orbit_camera and orbit_camera.has_method("set_camera_mode"):
		orbit_camera.set_camera_mode(OrbitCameraScript.CameraMode.MODE_CREATOR)

func _setup_tabs() -> void:
	var tabs = [body_tab_btn, skin_tab_btn, eyes_tab_btn, hair_tab_btn]
	for i in range(tabs.size()):
		var idx = i
		var btn = tabs[i]
		if btn:
			btn.pressed.connect(func(): _select_tab(idx))

func _select_tab(idx: int) -> void:
	var pages = [body_page, skin_page, eyes_page, hair_page]
	var tab_btns = [body_tab_btn, skin_tab_btn, eyes_tab_btn, hair_tab_btn]
	
	for i in range(pages.size()):
		if pages[i]:
			pages[i].visible = (i == idx)
		if tab_btns[i]:
			tab_btns[i].button_pressed = (i == idx)

func _setup_signals() -> void:
	if shoulder_slider:
		shoulder_slider.value_changed.connect(_on_shoulder_slider_changed)
	if height_slider:
		height_slider.value_changed.connect(_on_height_slider_changed)
		
	if eye_brightness_slider:
		eye_brightness_slider.value_changed.connect(_on_eye_brightness_changed)
	if eye_saturation_slider:
		eye_saturation_slider.value_changed.connect(_on_eye_saturation_changed)
		
	if hair_brightness_slider:
		hair_brightness_slider.value_changed.connect(_on_hair_brightness_changed)
	if hair_saturation_slider:
		hair_saturation_slider.value_changed.connect(_on_hair_saturation_changed)
	if hair_depth_slider:
		hair_depth_slider.value_changed.connect(_on_hair_depth_changed)
	if hair_height_slider:
		hair_height_slider.value_changed.connect(_on_hair_height_changed)
		
	if turntable_check:
		turntable_check.toggled.connect(_on_turntable_toggled)

	if test_walk_btn:
		test_walk_btn.pressed.connect(_enter_walk_mode)
	if exit_walk_btn:
		exit_walk_btn.pressed.connect(_exit_walk_mode)

	%FocusFaceBtn.pressed.connect(func(): if orbit_camera and orbit_camera.has_method("focus_face"): orbit_camera.focus_face())
	%FocusTorsoBtn.pressed.connect(func(): if orbit_camera and orbit_camera.has_method("focus_torso"): orbit_camera.focus_torso())
	%FocusFullBtn.pressed.connect(func(): if orbit_camera and orbit_camera.has_method("focus_full_body"): orbit_camera.focus_full_body())
	%ResetBtn.pressed.connect(_on_reset_pressed)

func _create_skin_swatches() -> void:
	if not skin_colors_container:
		return
	for child in skin_colors_container.get_children():
		child.queue_free()
	skin_swatch_buttons.clear()

	for c_name in SKIN_PRESETS:
		var col: Color = SKIN_PRESETS[c_name]
		var btn = _create_swatch_button(c_name, col)
		btn.pressed.connect(func():
			active_skin_name = c_name
			_refresh_swatch_selection(skin_swatch_buttons, active_skin_name)
			if character and character.has_method("set_skin_color"):
				character.set_skin_color(col)
		)
		skin_colors_container.add_child(btn)
		skin_swatch_buttons[c_name] = btn

	_refresh_swatch_selection(skin_swatch_buttons, active_skin_name)

func _create_eye_swatches() -> void:
	if not eye_colors_container:
		return
	for child in eye_colors_container.get_children():
		child.queue_free()
	eye_swatch_buttons.clear()

	for c_name in EYE_PRESETS:
		var col: Color = EYE_PRESETS[c_name]
		var btn = _create_swatch_button(c_name, col)
		btn.pressed.connect(func():
			active_eye_name = c_name
			_refresh_swatch_selection(eye_swatch_buttons, active_eye_name)
			if character and character.has_method("set_eye_color"):
				character.set_eye_color(col)
		)
		eye_colors_container.add_child(btn)
		eye_swatch_buttons[c_name] = btn

	_refresh_swatch_selection(eye_swatch_buttons, active_eye_name)

func _create_hair_style_buttons() -> void:
	if not hair_buttons_container or not character:
		return
	for child in hair_buttons_container.get_children():
		child.queue_free()
	hair_style_buttons.clear()

	var defs = character.get("MODULAR_HAIR_DEFS")
	if not defs:
		return

	for i in range(defs.size()):
		var idx = i
		var d = defs[i]
		var btn = Button.new()
		btn.text = d.name
		btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
		btn.custom_minimum_size = Vector2(0, 36)
		btn.toggle_mode = true
		btn.pressed.connect(func():
			active_hair_style_idx = idx
			_refresh_hair_style_selection()
			if character and character.has_method("set_hair_style"):
				character.set_hair_style(idx)
		)
		hair_buttons_container.add_child(btn)
		hair_style_buttons.append(btn)

	_refresh_hair_style_selection()

func _create_hair_color_swatches() -> void:
	if not hair_colors_container:
		return
	for child in hair_colors_container.get_children():
		child.queue_free()
	hair_swatch_buttons.clear()

	for c_name in HAIR_PRESETS:
		var col: Color = HAIR_PRESETS[c_name]
		var btn = _create_swatch_button(c_name, col)
		btn.pressed.connect(func():
			active_hair_color_name = c_name
			_refresh_swatch_selection(hair_swatch_buttons, active_hair_color_name)
			if character and character.has_method("set_hair_color"):
				character.set_hair_color(col)
		)
		hair_colors_container.add_child(btn)
		hair_swatch_buttons[c_name] = btn

	_refresh_swatch_selection(hair_swatch_buttons, active_hair_color_name)

func _create_swatch_button(swatch_name: String, color: Color) -> Button:
	var btn = Button.new()
	btn.custom_minimum_size = Vector2(44, 44)
	btn.tooltip_text = swatch_name
	
	# Create circular swatch box
	var style = StyleBoxFlat.new()
	style.bg_color = color
	style.set_corner_radius_all(22)
	style.border_color = Color(0.25, 0.30, 0.40, 0.8)
	style.set_border_width_all(2)
	
	btn.add_theme_stylebox_override("normal", style)
	
	var hover_style = style.duplicate()
	hover_style.border_color = Color(1.0, 1.0, 1.0, 0.9)
	hover_style.set_border_width_all(3)
	btn.add_theme_stylebox_override("hover", hover_style)
	
	return btn

func _refresh_swatch_selection(buttons_dict: Dictionary, active_key: String) -> void:
	for k in buttons_dict:
		var btn: Button = buttons_dict[k]
		var normal_style = btn.get_theme_stylebox("normal") as StyleBoxFlat
		if normal_style:
			if k == active_key:
				normal_style.border_color = Color(0.96, 0.82, 0.35, 1.0) # Gold active ring
				normal_style.set_border_width_all(3)
				normal_style.shadow_color = Color(0.96, 0.82, 0.35, 0.5)
				normal_style.shadow_size = 4
			else:
				normal_style.border_color = Color(0.25, 0.30, 0.40, 0.8)
				normal_style.set_border_width_all(2)
				normal_style.shadow_size = 0

func _refresh_hair_style_selection() -> void:
	for i in range(hair_style_buttons.size()):
		var btn = hair_style_buttons[i]
		btn.button_pressed = (i == active_hair_style_idx)

func _on_shoulder_slider_changed(value: float) -> void:
	if character and character.has_method("set_shoulder_width"):
		character.set_shoulder_width(value)
	_update_labels()

func _on_height_slider_changed(value: float) -> void:
	if character and character.has_method("set_height_scale"):
		character.set_height_scale(value)
	_update_labels()

func _on_eye_brightness_changed(value: float) -> void:
	if character and character.has_method("set_eye_brightness"):
		character.set_eye_brightness(value)
	_update_labels()

func _on_eye_saturation_changed(value: float) -> void:
	if character and character.has_method("set_eye_saturation"):
		character.set_eye_saturation(value)
	_update_labels()

func _on_hair_brightness_changed(value: float) -> void:
	if character and character.has_method("set_hair_brightness"):
		character.set_hair_brightness(value)
	_update_labels()

func _on_hair_saturation_changed(value: float) -> void:
	if character and character.has_method("set_hair_saturation"):
		character.set_hair_saturation(value)
	_update_labels()

func _on_hair_depth_changed(value: float) -> void:
	if hair_depth_label:
		hair_depth_label.text = "%+.1fmm" % (value * 1000.0)
	if character and character.has_method("set_hair_fitting"):
		character.set_hair_fitting(value, hair_height_slider.value if hair_height_slider else 0.0)

func _on_hair_height_changed(value: float) -> void:
	if hair_height_label:
		hair_height_label.text = "%+.1fmm" % (value * 1000.0)
	if character and character.has_method("set_hair_fitting"):
		character.set_hair_fitting(hair_depth_slider.value if hair_depth_slider else 0.0, value)

func _on_turntable_toggled(button_pressed: bool) -> void:
	if orbit_camera:
		orbit_camera.set("auto_rotate", button_pressed)

func _on_reset_pressed() -> void:
	if shoulder_slider:
		shoulder_slider.value = 1.0
	if height_slider:
		height_slider.value = 1.0
	if eye_brightness_slider:
		eye_brightness_slider.value = 1.0
	if eye_saturation_slider:
		eye_saturation_slider.value = 1.0
	if hair_brightness_slider:
		hair_brightness_slider.value = 1.0
	if hair_saturation_slider:
		hair_saturation_slider.value = 1.0
	if hair_depth_slider:
		hair_depth_slider.value = 0.0
	if hair_height_slider:
		hair_height_slider.value = 0.0
		
	active_skin_name = "Fair"
	active_eye_name = "Sapphire"
	active_hair_color_name = "Default"
	active_hair_style_idx = 0
	
	_refresh_swatch_selection(skin_swatch_buttons, active_skin_name)
	_refresh_swatch_selection(eye_swatch_buttons, active_eye_name)
	_refresh_swatch_selection(hair_swatch_buttons, active_hair_color_name)
	_refresh_hair_style_selection()
	
	if character:
		if character.has_method("set_skin_color"):
			character.set_skin_color(Color(1.0, 1.0, 1.0))
		if character.has_method("set_eye_color"):
			character.set_eye_color(Color(0.18, 0.45, 0.85))
		if character.has_method("set_eye_brightness"):
			character.set_eye_brightness(1.0)
		if character.has_method("set_eye_saturation"):
			character.set_eye_saturation(1.0)
		if character.has_method("set_hair_color"):
			character.set_hair_color(Color(1.0, 1.0, 1.0))
		if character.has_method("set_hair_brightness"):
			character.set_hair_brightness(1.0)
		if character.has_method("set_hair_saturation"):
			character.set_hair_saturation(1.0)
		if character.has_method("set_hair_fitting"):
			character.set_hair_fitting(0.0, 0.0)
		if character.has_method("set_hair_style"):
			character.set_hair_style(0)
	if orbit_camera and orbit_camera.has_method("reset_view"):
		orbit_camera.reset_view()
	_update_labels()

func _update_labels() -> void:
	if shoulder_label and shoulder_slider:
		shoulder_label.text = "%.2fx" % shoulder_slider.value
	if height_label and height_slider:
		height_label.text = "%.2fx" % height_slider.value
	if eye_brightness_label and eye_brightness_slider:
		eye_brightness_label.text = "%.2fx" % eye_brightness_slider.value
	if eye_saturation_label and eye_saturation_slider:
		eye_saturation_label.text = "%.2fx" % eye_saturation_slider.value
	if hair_brightness_label and hair_brightness_slider:
		hair_brightness_label.text = "%.2fx" % hair_brightness_slider.value
	if hair_saturation_label and hair_saturation_slider:
		hair_saturation_label.text = "%.2fx" % hair_saturation_slider.value
	if hair_depth_label and hair_depth_slider:
		hair_depth_label.text = "%+.1fmm" % (hair_depth_slider.value * 1000.0)
	if hair_height_label and hair_height_slider:
		hair_height_label.text = "%+.1fmm" % (hair_height_slider.value * 1000.0)

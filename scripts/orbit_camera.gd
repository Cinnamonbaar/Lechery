extends Camera3D
class_name OrbitCamera

enum CameraMode {
	MODE_CREATOR,
	MODE_WALK
}

@export var target_node: Node3D
@export var target_offset: Vector3 = Vector3(0.0, 1.05, 0.0)
@export var distance: float = 1.9
@export var min_distance: float = 0.5
@export var max_distance: float = 4.5

@export var mouse_sensitivity: float = 0.003
@export var zoom_speed: float = 0.25
@export var smoothness: float = 14.0
@export var auto_rotate: bool = false
@export var auto_rotate_speed: float = 0.35

var current_mode: int = CameraMode.MODE_CREATOR

var _yaw: float = 0.0
var _pitch: float = 0.0
var _target_yaw: float = 0.0
var _target_pitch: float = 0.0
var _target_distance: float = 1.9
var _current_offset: Vector3 = Vector3(0.0, 1.05, 0.0)
var _target_offset_pos: Vector3 = Vector3(0.0, 1.05, 0.0)

var _is_dragging: bool = false
var _is_panning: bool = false

func _ready() -> void:
	near = 0.05
	cull_mask = 3 # Layer 1 (World & Body) | Layer 2 (Head & Hair)
	_target_distance = distance
	_target_offset_pos = target_offset
	_current_offset = target_offset
	_yaw = rotation.y
	_pitch = rotation.x
	_target_yaw = _yaw
	_target_pitch = _pitch

func is_in_first_person() -> bool:
	return (current_mode == CameraMode.MODE_WALK and _target_distance <= 0.05)

func set_camera_mode(mode: int) -> void:
	current_mode = mode
	if current_mode == CameraMode.MODE_WALK:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		_target_offset_pos = Vector3(0.0, 1.35, 0.0)
		_target_distance = 2.0
		_is_dragging = false
		_is_panning = false
	else:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		_target_offset_pos = target_offset
		_target_distance = 1.9
		cull_mask = 3 # Ensure full avatar is visible in creator mode

func _unhandled_input(event: InputEvent) -> void:
	if current_mode == CameraMode.MODE_WALK:
		_handle_walk_input(event)
	else:
		_handle_creator_input(event)

func _handle_creator_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT or event.button_index == MOUSE_BUTTON_RIGHT:
			_is_dragging = event.pressed
		elif event.button_index == MOUSE_BUTTON_MIDDLE:
			_is_panning = event.pressed
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_target_distance = clamp(_target_distance - zoom_speed, min_distance, max_distance)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_target_distance = clamp(_target_distance + zoom_speed, min_distance, max_distance)

	elif event is InputEventMouseMotion:
		if _is_dragging:
			_target_yaw -= event.relative.x * (mouse_sensitivity * 1.5)
			_target_pitch -= event.relative.y * (mouse_sensitivity * 1.5)
			_target_pitch = clamp(_target_pitch, deg_to_rad(-75.0), deg_to_rad(75.0))
		elif _is_panning:
			var pan_speed: float = 0.002 * _target_distance
			_target_offset_pos.y += event.relative.y * pan_speed
			_target_offset_pos.y = clamp(_target_offset_pos.y, 0.2, 1.8)

func _handle_walk_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		_target_yaw -= event.relative.x * mouse_sensitivity
		_target_pitch -= event.relative.y * mouse_sensitivity
		# In walk mode, allow looking steep down (-80 deg) to clearly see player body/chest/feet
		_target_pitch = clamp(_target_pitch, deg_to_rad(-80.0), deg_to_rad(80.0))

	elif event is InputEventMouseButton:
		# Mouse wheel smooth hybrid Skyrim zoom
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			if _target_distance <= 0.4:
				# Snap directly into True First Person
				_target_distance = 0.0
				_target_offset_pos = Vector3(0.0, 1.48, 0.0) # Eye level
			else:
				_target_distance = max(0.0, _target_distance - zoom_speed)
				
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			if _target_distance <= 0.05:
				# Step back into 3rd person follow
				_target_distance = 0.8
				_target_offset_pos = Vector3(0.0, 1.35, 0.0)
			else:
				_target_distance = min(max_distance, _target_distance + zoom_speed)

func _process(delta: float) -> void:
	if current_mode == CameraMode.MODE_CREATOR and auto_rotate and not _is_dragging:
		_target_yaw += auto_rotate_speed * delta

	# Smooth damping interpolation
	_yaw = lerp_angle(_yaw, _target_yaw, delta * smoothness)
	_pitch = lerp(_pitch, _target_pitch, delta * smoothness)
	distance = lerp(distance, _target_distance, delta * smoothness)
	_current_offset = _current_offset.lerp(_target_offset_pos, delta * smoothness)

	var center: Vector3 = target_node.global_position if target_node else Vector3.ZERO
	center += _current_offset

	# Check First-Person state
	if is_in_first_person():
		# Layer 1 only: omits Layer 2 head/hair, keeping player's own body fully visible!
		cull_mask = 1
		near = 0.01 # Drastically reduce near plane "force field" (1cm) to prevent body clipping
		var live_neck: Vector3
		if target_node and target_node.has_method("get_neck_global_position"):
			live_neck = target_node.get_neck_global_position()
		else:
			live_neck = (target_node.global_position if target_node else Vector3.ZERO) + Vector3(0.0, 1.34, 0.0)
		var head_rot: Basis = Basis.from_euler(Vector3(_pitch, _yaw, 0.0))
		var eye_offset: Vector3 = Vector3(0.0, 0.14, -0.12)
		global_position = live_neck + head_rot * eye_offset
		transform.basis = head_rot
	else:
		near = 0.05
		# Third-Person or Creator: full head, hair, body, and world visible
		cull_mask = 3
		# In third-person orbit: pitch tilts up/down around character
		var orbit_pitch: float = -_pitch if current_mode == CameraMode.MODE_WALK else _pitch
		var pos: Vector3 = Vector3(
			sin(_yaw) * cos(orbit_pitch),
			sin(orbit_pitch),
			cos(_yaw) * cos(orbit_pitch)
		) * max(0.2, distance)

		global_position = center + pos
		look_at(center, Vector3.UP)

func focus_face() -> void:
	_target_offset_pos = Vector3(0.0, 1.35, 0.0)
	_target_distance = 0.75
	_target_pitch = deg_to_rad(0.0)

func focus_torso() -> void:
	_target_offset_pos = Vector3(0.0, 1.1, 0.0)
	_target_distance = 1.2
	_target_pitch = deg_to_rad(-5.0)

func focus_full_body() -> void:
	_target_offset_pos = Vector3(0.0, 0.85, 0.0)
	_target_distance = 2.2
	_target_pitch = deg_to_rad(-5.0)

func reset_view() -> void:
	_target_offset_pos = Vector3(0.0, 1.05, 0.0)
	_target_distance = 1.9
	_target_yaw = 0.0
	_target_pitch = 0.0

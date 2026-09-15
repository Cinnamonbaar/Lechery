shader_type spatial;
render_mode blend_mix, cull_front, unshaded;

uniform vec4 outline_color : source_color = vec4(0.15, 0.1, 0.12, 1.0);
uniform float outline_width : hint_range(0.0, 10.0) = 2.0;

void vertex() {
	// Inverted Hull method: push vertices outward along normal
	VERTEX += NORMAL * outline_width * 0.001;
}

void fragment() {
	ALBEDO = outline_color.rgb;
}

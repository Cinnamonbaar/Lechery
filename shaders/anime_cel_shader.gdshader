shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_toon, specular_toon;

uniform vec4 albedo_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 shadow_tint : source_color = vec4(0.82, 0.75, 0.85, 1.0);
uniform float rim_intensity : hint_range(0.0, 1.0) = 0.35;
uniform float rim_threshold : hint_range(0.0, 1.0) = 0.65;
uniform vec4 rim_color : source_color = vec4(1.0, 0.98, 0.92, 1.0);
uniform float specular_size : hint_range(0.0, 1.0) = 0.15;
uniform float roughness : hint_range(0.0, 1.0) = 0.4;

void fragment() {
	vec4 tex_color = texture(albedo_texture, UV);
	vec4 base = tex_color * albedo_color;
	ALBEDO = base.rgb;
	ALPHA = base.a;
	ROUGHNESS = roughness;
	SPECULAR = specular_size;
	
	// Subtle rim light calculation
	float n_dot_v = 1.0 - dot(NORMAL, VIEW);
	float rim = smoothstep(rim_threshold, rim_threshold + 0.1, n_dot_v) * rim_intensity;
	EMISSION = rim_color.rgb * rim;
}

void light() {
	// Stepped lighting calculation for anime cel shading
	float n_dot_l = dot(NORMAL, LIGHT);
	float light_intensity = smoothstep(0.0, 0.08, n_dot_l);
	
	vec3 light_color = LIGHT_COLOR * ATTENUATION;
	vec3 shadowed_albedo = ALBEDO * shadow_tint.rgb;
	vec3 final_albedo = mix(shadowed_albedo, ALBEDO, light_intensity);
	
	DIFFUSE_LIGHT += final_albedo * light_color;
}

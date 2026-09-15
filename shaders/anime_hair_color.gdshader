shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_toon, specular_toon;

uniform vec4 hair_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform vec4 orig_color : source_color = vec4(1.0, 1.0, 1.0, 1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform float brightness : hint_range(0.2, 3.0) = 1.0;
uniform float saturation : hint_range(0.0, 2.5) = 1.0;
uniform float contrast : hint_range(0.5, 2.0) = 1.0;
uniform float alpha_scissor_threshold : hint_range(0.0, 1.0) = 0.5;

uniform vec4 shadow_tint : source_color = vec4(0.82, 0.75, 0.85, 1.0);
uniform float rim_intensity : hint_range(0.0, 1.0) = 0.25;
uniform float rim_threshold : hint_range(0.0, 1.0) = 0.65;
uniform vec4 rim_color : source_color = vec4(1.0, 0.98, 0.92, 1.0);

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void fragment() {
    vec4 tex = texture(albedo_texture, UV);
    if (tex.a < alpha_scissor_threshold) {
        discard;
    }
    
    // Check if hair_color is non-white (user picked a custom preset)
    float is_custom = step(0.02, distance(hair_color.rgb, vec3(1.0)));
    vec3 active_tint = mix(orig_color.rgb, hair_color.rgb, is_custom);
    
    // Extract normalized luminance curve from texture
    float lum = dot(tex.rgb, vec3(0.299, 0.587, 0.114));
    float norm_lum = pow(clamp(lum * 1.8, 0.12, 1.0), contrast);
    
    // Apply tinting with shading contrast
    vec3 colored = active_tint * (norm_lum * 0.85 + 0.15);
    
    // Adjust HSV (Saturation & Brightness)
    vec3 hsv = rgb2hsv(colored);
    hsv.y = clamp(hsv.y * saturation, 0.0, 1.0);
    hsv.z = clamp(hsv.z * brightness, 0.0, 1.5);
    
    ALBEDO = hsv2rgb(hsv);
    ALPHA = tex.a;
    ALPHA_SCISSOR_THRESHOLD = alpha_scissor_threshold;
    ROUGHNESS = 0.5;
    SPECULAR = 0.15;
    
    // Subtle rim lighting
    float n_dot_v = 1.0 - dot(NORMAL, VIEW);
    float rim = smoothstep(rim_threshold, rim_threshold + 0.1, n_dot_v) * rim_intensity;
    EMISSION = rim_color.rgb * rim;
}

void light() {
    float n_dot_l = dot(NORMAL, LIGHT);
    float light_intensity = smoothstep(0.0, 0.08, n_dot_l);
    
    vec3 light_color = LIGHT_COLOR * ATTENUATION;
    vec3 shadowed_albedo = ALBEDO * shadow_tint.rgb;
    vec3 final_albedo = mix(shadowed_albedo, ALBEDO, light_intensity);
    
    DIFFUSE_LIGHT += final_albedo * light_color;
}

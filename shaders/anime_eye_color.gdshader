shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, unshaded;

uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform vec4 eye_tint : source_color = vec4(0.2, 0.55, 1.0, 1.0);
uniform float brightness : hint_range(0.0, 3.0) = 1.0;
uniform float saturation : hint_range(0.0, 2.5) = 1.0;
uniform float contrast : hint_range(0.5, 2.5) = 1.1;
uniform float tint_mix : hint_range(0.0, 1.0) = 0.9;

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
    if (tex.a < 0.05) discard;
    
    // Extract base brightness from dark iris drawing and normalize
    float lum = max(tex.r, max(tex.g, tex.b));
    float normalized_lum = pow(clamp(lum * 4.5, 0.0, 1.0), contrast);
    
    // Tint with target eye color
    vec3 colored = eye_tint.rgb * (normalized_lum * 0.9 + 0.1);
    vec3 blended = mix(tex.rgb, colored, tint_mix);
    
    // Apply saturation & brightness
    vec3 hsv = rgb2hsv(blended);
    hsv.y = clamp(hsv.y * saturation, 0.0, 1.0);
    hsv.z = clamp(hsv.z * brightness, 0.0, 2.0);
    
    ALBEDO = hsv2rgb(hsv);
    ALPHA = tex.a;
}

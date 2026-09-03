uniform sampler2D uMap;
uniform float uHoverMix;
uniform vec3 uRestDark;
uniform vec3 uRestLight;
uniform vec3 uHoverDark;
uniform vec3 uHoverLight;

varying vec2 vUv;
varying vec3 vViewNormal;

void main() {
  vec4 source = texture2D(uMap, vUv);

  float sourceMax = max(max(source.r, source.g), source.b);
  float sourceMin = min(min(source.r, source.g), source.b);
  float chroma = sourceMax - sourceMin;
  float grayscaleMask = 1.0 - smoothstep(0.035, 0.16, chroma);
  float luminance = dot(source.rgb, vec3(0.2126, 0.7152, 0.0722));
  float lightPart = smoothstep(0.08, 0.72, luminance);

  vec3 darkColor = mix(uRestDark, uHoverDark, uHoverMix);
  vec3 lightColor = mix(uRestLight, uHoverLight, uHoverMix);
  vec3 paletteColor = mix(darkColor, lightColor, lightPart);

  // Recolor the controller's black/gray shell while preserving the colored
  // Xbox button details from the original texture.
  vec3 baseColor = mix(source.rgb, paletteColor, grayscaleMask * 0.96);

  vec3 normal = normalize(vViewNormal);
  vec3 softLightDirection = normalize(vec3(-0.35, 0.55, 0.76));
  float diffuse = 0.82 + 0.18 * max(dot(normal, softLightDirection), 0.0);
  float rim = pow(1.0 - abs(normal.z), 2.0) * 0.06;

  gl_FragColor = vec4(baseColor * (diffuse + rim), source.a);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}

uniform vec3 uDayColor;
uniform vec3 uNightColor;
uniform float uThemeMix;
uniform float uPolish;

varying vec3 vViewNormal;

void main() {
  vec3 normal = normalize(vViewNormal);
  vec3 lightDirection = normalize(vec3(-0.35, 0.58, 0.74));
  vec3 viewDirection = vec3(0.0, 0.0, 1.0);
  vec3 halfDirection = normalize(lightDirection + viewDirection);
  float diffuse = 0.84 + 0.16 * max(dot(normal, lightDirection), 0.0);
  float rim = pow(1.0 - abs(normal.z), 2.0) * 0.045;
  float specular = pow(max(dot(normal, halfDirection), 0.0), 32.0) * uPolish;
  vec3 color = mix(uDayColor, uNightColor, uThemeMix);

  gl_FragColor = vec4(color * (diffuse + rim) + vec3(specular), 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}

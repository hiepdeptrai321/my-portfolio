uniform sampler2D uDayTexture;
uniform vec3 uNightTint;
uniform float uThemeMix;

varying vec2 vPcUv;

void main() {
  vec3 dayColor = texture2D(uDayTexture, vPcUv).rgb;
  vec3 color = mix(dayColor, dayColor * uNightTint, uThemeMix);

  gl_FragColor = vec4(color, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}

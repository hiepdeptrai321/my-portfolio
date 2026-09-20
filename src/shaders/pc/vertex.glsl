varying vec2 vPcUv;

void main() {
  vPcUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}

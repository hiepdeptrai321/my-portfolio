uniform vec3 uLightDirectionWorld;

varying vec3 vNormalView;
varying vec3 vViewPosition;
varying vec3 vLightDirectionView;
varying vec3 vUpView;

void main() {
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);

    vNormalView = normalize(normalMatrix * normal);
    vViewPosition = viewPosition.xyz;
    vLightDirectionView = normalize(mat3(viewMatrix) * uLightDirectionWorld);
    vUpView = normalize(mat3(viewMatrix) * vec3(0.0, 1.0, 0.0));

    gl_Position = projectionMatrix * viewPosition;
}

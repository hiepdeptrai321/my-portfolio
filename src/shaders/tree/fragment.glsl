uniform vec3 uDayColor;
uniform vec3 uNightColor;
uniform vec3 uSkyTint;
uniform vec3 uGroundTint;
uniform vec3 uMorningSpecularColor;
uniform float uThemeMix;
uniform float uOpacity;
uniform float uSpecularStrength;
uniform float uSpecularPower;

varying vec3 vNormalView;
varying vec3 vViewPosition;
varying vec3 vLightDirectionView;
varying vec3 vUpView;

void main() {
    vec3 normalView = normalize(vNormalView);

    #ifdef DOUBLE_SIDED
        normalView *= gl_FrontFacing ? 1.0 : -1.0;
    #endif

    vec3 viewDirection = normalize(-vViewPosition);
    vec3 baseColor = mix(uDayColor, uNightColor, uThemeMix);
    vec3 lightDirection = normalize(vLightDirectionView);
    float nDotL = max(dot(normalView, lightDirection), 0.0);

    float directional = smoothstep(
        -0.25,
        0.75,
        dot(normalView, lightDirection)
    );
    float hemisphere =
        dot(normalView, normalize(vUpView)) * 0.5 + 0.5;
    float rim = pow(
        1.0 - max(dot(normalView, viewDirection), 0.0),
        2.4
    );
    vec3 halfDirection = normalize(lightDirection + viewDirection);
    float specularLobe = pow(
        max(dot(normalView, halfDirection), 0.0),
        uSpecularPower
    );
    float morningAmount = 1.0 - smoothstep(0.0, 1.0, uThemeMix);
    vec3 morningSpecular =
        uMorningSpecularColor *
        uSpecularStrength *
        specularLobe *
        smoothstep(0.0, 0.2, nDotL) *
        morningAmount;

    vec3 hemisphereTint = mix(uGroundTint, uSkyTint, hemisphere);
    vec3 lighting =
        vec3(0.42) +
        hemisphereTint * 0.38 +
        vec3(directional * 0.28);
    float nightLightScale = mix(1.0, 0.72, uThemeMix);
    float rimStrength = mix(0.09, 0.025, uThemeMix);
    vec3 outgoingColor =
        baseColor * lighting * nightLightScale +
        baseColor * rim * rimStrength +
        morningSpecular;

    gl_FragColor = vec4(outgoingColor, uOpacity);

    #include <tonemapping_fragment>
    #include <colorspace_fragment>
}

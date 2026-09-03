uniform sampler2D uDayTexture1;
uniform sampler2D uNightTexture1;
uniform sampler2D uDayTexture2;
uniform sampler2D uNightTexture2;
uniform sampler2D uDayTexture3;
uniform sampler2D uNightTexture3;
uniform sampler2D uDayTexture4;
uniform sampler2D uNightTexture4;
uniform float uMixRatio;
uniform int uTextureSet;
uniform vec3 uGitHubLogoColor;
uniform vec3 uGitHubBackgroundColor;

varying vec2 vUv;
varying float vGitHubLogoMask;

void main() {
    vec3 dayColor;
    vec3 nightColor;

    if(uTextureSet == 1) {
        dayColor = texture2D(uDayTexture1, vUv).rgb;
        nightColor = texture2D(uNightTexture1, vUv).rgb;
    } else if(uTextureSet == 2) {
        dayColor = texture2D(uDayTexture2, vUv).rgb;
        nightColor = texture2D(uNightTexture2, vUv).rgb;
    } else if(uTextureSet == 3) {
        dayColor = texture2D(uDayTexture3, vUv).rgb;
        nightColor = texture2D(uNightTexture3, vUv).rgb;
    } else {
        dayColor = texture2D(uDayTexture4, vUv).rgb;
        nightColor = texture2D(uNightTexture4, vUv).rgb;
    }

    vec3 finalColor = mix(dayColor, nightColor, uMixRatio);
    float bakedLight = dot(finalColor, vec3(0.2126, 0.7152, 0.0722));
    float backgroundShade = mix(0.72, 1.12, smoothstep(0.02, 0.65, bakedLight));
    float logoShade = mix(0.82, 1.04, smoothstep(0.02, 0.55, bakedLight));
    vec3 backgroundColor = min(uGitHubBackgroundColor * backgroundShade, vec3(1.0));
    vec3 logoColor = min(uGitHubLogoColor * logoShade, vec3(1.0));
    finalColor = mix(backgroundColor, logoColor, step(0.5, vGitHubLogoMask));

    finalColor = pow(finalColor, vec3(1.0 / 2.2));
    gl_FragColor = vec4(finalColor, 1.0);
}

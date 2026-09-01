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
uniform vec3 uDayPinkBrown;
uniform vec3 uNightPinkBrown;

varying vec2 vUv;

float getLuminance(vec3 color) {
    return dot(color, vec3(0.2126, 0.7152, 0.0722));
}

vec3 rgbToHsv(vec3 color) {
    vec4 key = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 firstMix = mix(
        vec4(color.bg, key.wz),
        vec4(color.gb, key.xy),
        step(color.b, color.g)
    );
    vec4 secondMix = mix(
        vec4(firstMix.xyw, color.r),
        vec4(color.r, firstMix.yzx),
        step(firstMix.x, color.r)
    );
    float chroma = secondMix.x - min(secondMix.w, secondMix.y);
    float epsilon = 1.0e-10;

    return vec3(
        abs(
            secondMix.z +
            (secondMix.w - secondMix.y) / (6.0 * chroma + epsilon)
        ),
        chroma / (secondMix.x + epsilon),
        secondMix.x
    );
}

float getPinkAccentMask(vec3 displayColor) {
    vec3 hsv = rgbToHsv(displayColor);
    float pinkHue = smoothstep(0.82, 0.91, hsv.x);
    float enoughSaturation = smoothstep(0.12, 0.28, hsv.y);
    float redDominance = smoothstep(
        0.01,
        0.10,
        displayColor.r - displayColor.g
    );
    float blueSupport = smoothstep(
        -0.015,
        0.055,
        displayColor.b - displayColor.g
    );
    float visibleColor = smoothstep(0.06, 0.16, hsv.z);

    return pinkHue * enoughSaturation * redDominance * blueSupport * visibleColor;
}

vec3 recolorPinkAccent(vec3 sourceColor, vec3 brownColor) {
    vec3 displayColor = pow(
        max(sourceColor, vec3(0.0)),
        vec3(1.0 / 2.2)
    );
    float accentMask = getPinkAccentMask(displayColor);
    vec3 displayBrown = pow(
        max(brownColor, vec3(0.0)),
        vec3(1.0 / 2.2)
    );
    float sourceLuminance = getLuminance(displayColor);
    float brownLuminance = max(getLuminance(displayBrown), 0.0001);
    vec3 recoloredDisplay = clamp(
        displayBrown * (sourceLuminance / brownLuminance),
        0.0,
        1.0
    );
    vec3 recoloredLinear = pow(recoloredDisplay, vec3(2.2));

    return mix(sourceColor, recoloredLinear, accentMask);
}

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
    
    vec3 recoloredDay = recolorPinkAccent(dayColor, uDayPinkBrown);
    vec3 recoloredNight = recolorPinkAccent(nightColor, uNightPinkBrown);
    vec3 finalColor = mix(recoloredDay, recoloredNight, uMixRatio);

    finalColor = pow(finalColor, vec3(1.0 / 2.2));
    gl_FragColor = vec4(finalColor, 1.0);
}

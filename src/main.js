import gsap from "gsap";

import { Howl, Howler } from "howler";

import * as THREE from "three";
import { OrbitControls } from "./utils/orbit-controls.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

import smokeVertexShader from "./shaders/smoke/vertex.glsl";
import smokeFragmentShader from "./shaders/smoke/fragment.glsl";
import themeVertexShader from "./shaders/theme/vertex.glsl";
import themeFragmentShader from "./shaders/theme/fragment.glsl";
import treeVertexShader from "./shaders/tree/vertex.glsl";
import treeFragmentShader from "./shaders/tree/fragment.glsl";

import { StoryModal } from "./components/story-modal.js";
import { AmbientBackground } from "./components/ambient-background.js";
import {
  getInitialLanguage,
  getTranslation,
  SUPPORTED_LANGUAGES,
} from "./data/translations.js";

const ambientBackground = new AmbientBackground({
  canvas: document.querySelector(".ambient-background-canvas"),
});

/**  -------------------------- Audio setup -------------------------- */

// Background Music
let pianoDebounceTimer = null;
let isMusicFaded = false;
const MUSIC_FADE_TIME = 500;
const PIANO_TIMEOUT = 2000;
const BACKGROUND_MUSIC_VOLUME = 1;
const FADED_VOLUME = 0;
const DEFAULT_VOLUME = 0.4;
const HANDWRITING_ANIMATION_DURATION = 2.3;
const HANDWRITING_LETTER_STAGGER = 0.12;
const HANDWRITING_TIMING_VARIATION = [0, 0.018, -0.008, 0.012, -0.014];
const HANDWRITING_START_Y = [8, 11, 7, 10, 9];
const HANDWRITING_START_ROTATION = [-2.2, 1.1, -0.8, 1.6, -1.2];
const INTRO_DOOR_MUSIC_VOLUME = 0.22;
const INTRO_WRITING_MUSIC_VOLUME = 0.35;
const INTRO_MUSIC_FADE_TIME = 650;
const PAPER_EXIT_DURATION = 2;
const PAPER_EXIT_LIFT_DURATION = 0.35;

let currentLanguage = getInitialLanguage();
let currentVolume = DEFAULT_VOLUME;
let lastAudibleVolume = DEFAULT_VOLUME;
let isMuted = false;
let hasEnteredRoom = false;

Howler.volume(DEFAULT_VOLUME);

const backgroundMusic = new Howl({
  src: ["/audio/music/drawer-instrumental.mp3"],
  loop: true,
  volume: 1,
});

const fadeOutBackgroundMusic = () => {
  if (!isMuted && !isMusicFaded) {
    backgroundMusic.fade(
      backgroundMusic.volume(),
      FADED_VOLUME,
      MUSIC_FADE_TIME
    );
    isMusicFaded = true;
  }
};

const fadeInBackgroundMusic = () => {
  if (!isMuted && isMusicFaded) {
    backgroundMusic.fade(
      FADED_VOLUME,
      BACKGROUND_MUSIC_VOLUME,
      MUSIC_FADE_TIME
    );
    isMusicFaded = false;
  }
};

const setBackgroundMusicForWriting = () => {
  if (!isMuted) {
    backgroundMusic.fade(
      backgroundMusic.volume(),
      INTRO_WRITING_MUSIC_VOLUME,
      INTRO_MUSIC_FADE_TIME
    );
  }
};

const restoreBackgroundMusicAfterIntro = () => {
  if (!isMuted) {
    backgroundMusic.fade(
      backgroundMusic.volume(),
      BACKGROUND_MUSIC_VOLUME,
      INTRO_MUSIC_FADE_TIME
    );
  }
};

// Piano
const pianoKeyMap = {
  C1_Key: "key-24",
  "C#1_Key": "key-23",
  D1_Key: "key-22",
  "D#1_Key": "key-21",
  E1_Key: "key-20",
  F1_Key: "key-19",
  "F#1_Key": "key-18",
  G1_Key: "key-17",
  "G#1_Key": "key-16",
  A1_Key: "key-15",
  "A#1_Key": "key-14",
  B1_Key: "key-13",
  C2_Key: "key-12",
  "C#2_Key": "key-11",
  D2_Key: "key-10",
  "D#2_Key": "key-9",
  E2_Key: "key-8",
  F2_Key: "key-7",
  "F#2_Key": "key-6",
  G2_Key: "key-5",
  "G#2_Key": "key-4",
  A2_Key: "key-3",
  "A#2_Key": "key-2",
  B2_Key: "key-1",
};

const pianoSounds = {};

Object.values(pianoKeyMap).forEach((soundKey) => {
  pianoSounds[soundKey] = new Howl({
    src: [`/audio/sfx/piano/${soundKey}.ogg`],
    preload: true,
    volume: 0.5,
  });
});

// Button
const buttonSounds = {
  click: new Howl({
    src: ["/audio/sfx/click/bubble.ogg"],
    preload: true,
    volume: 0.5,
  }),
};

const introSounds = {
  writing: new Howl({
    src: ["/audio/sfx/writing.mp3"],
    preload: true,
    volume: 0.85,
    sprite: {
      opening: [0, HANDWRITING_ANIMATION_DURATION * 1000],
    },
  }),
  paperFlutter: new Howl({
    src: ["/audio/sfx/paperflutter.mp3"],
    preload: true,
    volume: 0.9,
  }),
};

const playHelloWritingSound = () => {
  introSounds.writing.play("opening");
  introSounds.writing.play("opening");
};

const playPaperExitSound = () => {
  introSounds.paperFlutter.play();
};

const playDoorOpenSound = () => {
  const audioContext = Howler.ctx;
  const audioDestination = Howler.masterGain;

  if (
    isMuted ||
    currentVolume <= 0 ||
    !audioContext ||
    !audioDestination
  ) {
    return;
  }

  const startTime = audioContext.currentTime;
  const creakDuration = 1.15;
  const creakBuffer = audioContext.createBuffer(
    1,
    Math.floor(audioContext.sampleRate * creakDuration),
    audioContext.sampleRate
  );
  const creakData = creakBuffer.getChannelData(0);
  let smoothedNoise = 0;

  for (let sampleIndex = 0; sampleIndex < creakData.length; sampleIndex += 1) {
    smoothedNoise =
      smoothedNoise * 0.94 + (Math.random() * 2 - 1) * 0.06;
    creakData[sampleIndex] = smoothedNoise;
  }

  const creakSource = audioContext.createBufferSource();
  const creakFilter = audioContext.createBiquadFilter();
  const creakGain = audioContext.createGain();

  creakSource.buffer = creakBuffer;
  creakSource.playbackRate.setValueAtTime(0.92, startTime);
  creakSource.playbackRate.exponentialRampToValueAtTime(
    0.62,
    startTime + creakDuration
  );
  creakFilter.type = "bandpass";
  creakFilter.frequency.setValueAtTime(210, startTime);
  creakFilter.frequency.exponentialRampToValueAtTime(
    430,
    startTime + creakDuration
  );
  creakFilter.Q.value = 0.8;
  creakGain.gain.setValueAtTime(0.0001, startTime);
  creakGain.gain.exponentialRampToValueAtTime(0.42, startTime + 0.08);
  creakGain.gain.exponentialRampToValueAtTime(
    0.0001,
    startTime + creakDuration
  );

  creakSource.connect(creakFilter);
  creakFilter.connect(creakGain);
  creakGain.connect(audioDestination);
  creakSource.start(startTime);
  creakSource.stop(startTime + creakDuration);

  const latchOscillator = audioContext.createOscillator();
  const latchGain = audioContext.createGain();

  latchOscillator.type = "triangle";
  latchOscillator.frequency.setValueAtTime(125, startTime);
  latchOscillator.frequency.exponentialRampToValueAtTime(52, startTime + 0.14);
  latchGain.gain.setValueAtTime(0.26, startTime);
  latchGain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.14);
  latchOscillator.connect(latchGain);
  latchGain.connect(audioDestination);
  latchOscillator.start(startTime);
  latchOscillator.stop(startTime + 0.15);
};

/**  -------------------------- Scene setup -------------------------- */
const canvas = document.querySelector("#experience-canvas");
const sizes = {
  width: window.innerWidth,
  height: window.innerHeight,
};

const scene = new THREE.Scene();
scene.background = new THREE.Color("#DCE2DE");

const camera = new THREE.PerspectiveCamera(
  35,
  sizes.width / sizes.height,
  0.1,
  200
);

const renderer = new THREE.WebGLRenderer({
  canvas: canvas,
  antialias: true,
});

renderer.setSize(sizes.width, sizes.height);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const controls = new OrbitControls(camera, renderer.domElement);
controls.minDistance = 5;
controls.maxDistance = 45;
controls.minPolarAngle = 0;
controls.maxPolarAngle = Math.PI / 2;
controls.minAzimuthAngle = 0;
controls.maxAzimuthAngle = Math.PI / 2;

controls.enableDamping = true;
controls.dampingFactor = 0.05;

controls.update();

//Set starting camera position
if (window.innerWidth < 768) {
  camera.position.set(
    29.567116827654726,
    14.018476147584705,
    31.37040363900147
  );
  controls.target.set(
    -0.08206262548844094,
    3.3119233527087255,
    -0.7433922282864018
  );
} else {
  camera.position.set(17.49173098423395, 9.108969527553887, 17.850992894238058);
  controls.target.set(
    0.4624746759408973,
    1.9719940043010387,
    -0.8300979125494505
  );
}

window.addEventListener("resize", () => {
  sizes.width = window.innerWidth;
  sizes.height = window.innerHeight;

  // Update Camera
  camera.aspect = sizes.width / sizes.height;
  camera.updateProjectionMatrix();

  // Update renderer
  renderer.setSize(sizes.width, sizes.height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
});

/**  -------------------------- Modal Stuff -------------------------- */
const modals = {
  work: document.querySelector(".modal.work"),
  about: document.querySelector(".modal.about"),
  contact: document.querySelector(".modal.contact"),
};

const overlay = document.querySelector(".overlay");

let hasTouchHappened = false;
let touchStartPosition = null;
let hasTouchMoved = false;
const TOUCH_MOVE_THRESHOLD = 12;
overlay.addEventListener(
  "touchend",
  (e) => {
    hasTouchHappened = true;
    e.preventDefault();
    const modal = document.querySelector('.modal[style*="display: block"]');
    if (modal) hideModal(modal);
  },
  { passive: false }
);

overlay.addEventListener(
  "click",
  (e) => {
    if (hasTouchHappened) return;
    e.preventDefault();
    const modal = document.querySelector('.modal[style*="display: block"]');
    if (modal) hideModal(modal);
  },
  { passive: false }
);

document.querySelectorAll(".modal-exit-button").forEach((button) => {
  function handleModalExit(e) {
    e.preventDefault();
    const modal = e.target.closest(".modal");

    gsap.to(button, {
      scale: 5,
      duration: 0.5,
      ease: "back.out(2)",
      onStart: () => {
        gsap.to(button, {
          scale: 1,
          duration: 0.5,
          ease: "back.out(2)",
          onComplete: () => {
            gsap.set(button, {
              clearProps: "all",
            });
          },
        });
      },
    });

    buttonSounds.click.play();
    hideModal(modal);
  }

  button.addEventListener(
    "touchend",
    (e) => {
      hasTouchHappened = true;
      handleModalExit(e);
    },
    { passive: false }
  );

  button.addEventListener(
    "click",
    (e) => {
      if (hasTouchHappened) return;
      handleModalExit(e);
    },
    { passive: false }
  );
});

let isModalOpen = true;

const showModal = (modal) => {
  modal.style.display = "block";
  overlay.style.display = "block";

  isModalOpen = true;
  controls.enabled = false;

  if (currentHoveredObject) {
    playHoverAnimation(currentHoveredObject, false);
    currentHoveredObject = null;
  }
  document.body.style.cursor = "default";
  currentIntersects = [];

  gsap.set(modal, {
    opacity: 0,
    scale: 0,
  });
  gsap.set(overlay, {
    opacity: 0,
  });

  gsap.to(overlay, {
    opacity: 1,
    duration: 0.5,
  });

  gsap.to(modal, {
    opacity: 1,
    scale: 1,
    duration: 0.5,
    ease: "back.out(2)",
  });
};

const hideModal = (modal) => {
  isModalOpen = false;
  controls.enabled = true;

  gsap.to(overlay, {
    opacity: 0,
    duration: 0.5,
  });

  gsap.to(modal, {
    opacity: 0,
    scale: 0,
    duration: 0.5,
    ease: "back.in(2)",
    onComplete: () => {
      modal.style.display = "none";
      overlay.style.display = "none";
    },
  });
};

const storyModal = new StoryModal({
  modalElement: document.querySelector(".modal.story"),
  onOpen: showModal,
  onClose: hideModal,
  initialLanguage: currentLanguage,
});

/**  -------------------------- Loading Screen & Intro Animation -------------------------- */

const manager = new THREE.LoadingManager();

const loadingScreen = document.querySelector(".loading-screen");
const loadingScreenButton = document.querySelector(".loading-screen-button");
const welcomeScreen = document.querySelector(".welcome-screen");
const welcomeScreenGreeting = document.querySelector(
  ".welcome-screen-greeting"
);
const welcomeScreenContent = document.querySelector(".welcome-screen-content");
const welcomeScreenAccent = document.querySelector(".welcome-screen-accent");
const leftDoorPanel = document.querySelector(".door-panel-left");
const rightDoorPanel = document.querySelector(".door-panel-right");
const languageToggleButton = document.querySelector(".language-toggle-button");
let loadingScreenState = "loading";

const translate = (key) => getTranslation(currentLanguage, key);

const updateSoundControlLabels = () => {
  const muteButton = document.querySelector(".mute-toggle-button");
  const volumeSlider = document.querySelector(".volume-slider");
  const volumeValue = document.querySelector(".volume-value");
  const volumePercentage = Math.round(currentVolume * 100);

  muteButton.setAttribute(
    "aria-label",
    translate(isMuted ? "controls.unmute" : "controls.mute")
  );
  muteButton.setAttribute("aria-pressed", String(isMuted));
  volumeSlider.setAttribute(
    "aria-valuetext",
    translate("controls.volumeValue")(volumePercentage)
  );
  volumeValue.textContent = `${volumePercentage}%`;
};

const applyLanguage = (language) => {
  if (!SUPPORTED_LANGUAGES.includes(language)) return;

  currentLanguage = language;
  document.documentElement.lang = language;
  document.body.dataset.language = language;
  document.title = translate("meta.title");

  document
    .querySelector('meta[name="description"]')
    .setAttribute("content", translate("meta.description"));
  document
    .querySelector('meta[property="og:title"]')
    .setAttribute("content", translate("meta.title"));
  document
    .querySelector('meta[property="og:description"]')
    .setAttribute("content", translate("meta.openGraphDescription"));

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const translatedValue = translate(element.dataset.i18n);
    if (typeof translatedValue === "string") {
      element.textContent = translatedValue;
    }
  });

  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    const translatedValue = translate(element.dataset.i18nAriaLabel);
    if (typeof translatedValue === "string") {
      element.setAttribute("aria-label", translatedValue);
    }
  });

  const loadingTranslationKey = {
    loading: "loading.loading",
    ready: "loading.enter",
    welcome: "loading.welcome",
  }[loadingScreenState];

  if (loadingScreenButton.isConnected) {
    loadingScreenButton.textContent = translate(loadingTranslationKey);
  }

  storyModal.setLanguage(language);
  updateSoundControlLabels();

  const languageUrl = new URL(window.location.href);
  languageUrl.searchParams.set("lang", language);
  window.history.replaceState({}, "", languageUrl);

};

languageToggleButton.addEventListener("click", () => {
  applyLanguage(currentLanguage === "en" ? "vi" : "en");
  buttonSounds.click.play();
});

applyLanguage(currentLanguage);

manager.onLoad = function () {
  loadingScreenState = "ready";
  loadingScreenButton.style.border = "8px solid #405D52";
  loadingScreenButton.style.background = "#718E7A";
  loadingScreenButton.style.color = "#F1E9DE";
  loadingScreenButton.style.boxShadow = "rgba(0, 0, 0, 0.24) 0px 3px 8px";
  loadingScreenButton.textContent = translate("loading.enter");
  loadingScreenButton.style.cursor = "pointer";
  loadingScreenButton.style.transition =
    "transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)";
  let isDisabled = false;

  function handleEnter() {
    if (isDisabled) return;

    loadingScreenState = "welcome";
    hasEnteredRoom = true;
    loadingScreenButton.style.cursor = "default";
    loadingScreenButton.style.border = "8px solid #718E7A";
    loadingScreenButton.style.background = "#DCE2DE";
    loadingScreenButton.style.color = "#405D52";
    loadingScreenButton.style.boxShadow = "none";
    loadingScreenButton.textContent = translate("loading.welcome");
    loadingScreen.style.background = "#F1E9DE";
    isDisabled = true;

    prepareWelcomeScreen();

    toggleFavicons();

    if (Howler.ctx?.state === "suspended") {
      Howler.ctx.resume();
    }
    backgroundMusic.volume(INTRO_DOOR_MUSIC_VOLUME);
    backgroundMusic.play();

    playReveal();
  }

  loadingScreenButton.addEventListener("mouseenter", () => {
    loadingScreenButton.style.transform = "scale(1.3)";
  });

  loadingScreenButton.addEventListener("touchend", (e) => {
    hasTouchHappened = true;
    e.preventDefault();
    handleEnter();
  });

  loadingScreenButton.addEventListener("click", (e) => {
    if (hasTouchHappened) return;
    handleEnter();
  });

  loadingScreenButton.addEventListener("mouseleave", () => {
    loadingScreenButton.style.transform = "none";
  });
};

function playReveal() {
  gsap.to(loadingScreen, {
    opacity: 0,
    scale: 0.995,
    duration: 0.25,
    ease: "power2.inOut",
    onComplete: () => {
      loadingScreen.remove();
      playWelcomeSequence();
    },
  });
}

function renderWelcomeLetters() {
  const greeting = welcomeScreenGreeting.textContent.trim();
  const segmenter =
    typeof Intl.Segmenter === "function"
      ? new Intl.Segmenter(undefined, { granularity: "grapheme" })
      : null;
  const characters = segmenter
    ? Array.from(segmenter.segment(greeting), ({ segment }) => segment)
    : Array.from(greeting);
  const letterFragment = document.createDocumentFragment();

  welcomeScreenGreeting.setAttribute("aria-label", greeting);

  characters.forEach((character) => {
    const letter = document.createElement("span");
    letter.className = "welcome-letter";
    letter.setAttribute("aria-hidden", "true");
    letter.textContent = character === " " ? "\u00a0" : character;
    letterFragment.append(letter);
  });

  welcomeScreenGreeting.replaceChildren(letterFragment);
  return welcomeScreenGreeting.querySelectorAll(".welcome-letter");
}

function prepareWelcomeScreen() {
  welcomeScreen.style.display = "grid";
  welcomeScreen.setAttribute("aria-hidden", "false");

  const welcomeLetters = renderWelcomeLetters();

  gsap.set(welcomeScreen, { opacity: 1 });
  gsap.set(welcomeScreenContent, {
    opacity: 1,
    x: 0,
    xPercent: 0,
    y: 0,
    scale: 1,
    rotationX: 0,
    rotationY: 0,
    rotationZ: 0,
  });
  gsap.set(leftDoorPanel, {
    rotationY: 0,
    transformOrigin: "left center",
  });
  gsap.set(rightDoorPanel, {
    rotationY: 0,
    transformOrigin: "right center",
  });
  gsap.set(welcomeLetters, {
    opacity: 0,
    y: (index) => HANDWRITING_START_Y[index % HANDWRITING_START_Y.length],
    rotation: (index) =>
      HANDWRITING_START_ROTATION[index % HANDWRITING_START_ROTATION.length],
    filter: "blur(3px)",
    clipPath: "inset(0 100% 0 0)",
    transformOrigin: "left center",
  });
  gsap.set(welcomeScreenAccent, {
    opacity: 0,
    scaleX: 0,
  });
}

function playWelcomeSequence() {
  const shouldReduceMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  const finishWelcome = () => {
    welcomeScreen.setAttribute("aria-hidden", "true");
    welcomeScreen.style.display = "none";
    isModalOpen = false;
    restoreBackgroundMusicAfterIntro();
    playIntroAnimation();
  };

  const welcomeLetters = welcomeScreenGreeting.querySelectorAll(
    ".welcome-letter"
  );

  if (shouldReduceMotion) {
    gsap
      .timeline({ onComplete: finishWelcome })
      .addLabel("door-open")
      .call(playDoorOpenSound, [], "door-open")
      .to(
        leftDoorPanel,
        { rotationY: -78, duration: 0.4, ease: "power1.inOut" },
        "door-open"
      )
      .to(
        rightDoorPanel,
        { rotationY: 78, duration: 0.4, ease: "power1.inOut" },
        "door-open"
      )
      .set(welcomeLetters, {
        opacity: 1,
        y: 0,
        filter: "blur(0px)",
        rotation: 0,
      })
      .set(welcomeScreenAccent, { opacity: 1, scaleX: 1 })
      .call(setBackgroundMusicForWriting)
      .addLabel("reduced-paper-exit", "+=0.65")
      .call(playPaperExitSound, [], "reduced-paper-exit-=0.5")
      .to(
        welcomeScreenContent,
        {
          opacity: 0,
          yPercent: -8,
          rotationZ: 3,
          duration: 0.35,
          ease: "power1.inOut",
        },
        "reduced-paper-exit"
      );
    return;
  }

  const welcomeTimeline = gsap.timeline({ onComplete: finishWelcome });

  welcomeTimeline
    .addLabel("door-open")
    .call(playDoorOpenSound, [], "door-open")
    .to(
      leftDoorPanel,
      {
        rotationY: -88,
        duration: 1.2,
        ease: "power3.inOut",
      },
      "door-open"
    )
    .to(
      rightDoorPanel,
      {
        rotationY: 88,
        duration: 1.2,
        ease: "power3.inOut",
      },
      "door-open"
    )
    .addLabel("handwriting", "door-open+=0.95")
    .call(setBackgroundMusicForWriting, [], "handwriting")
    .call(playHelloWritingSound, [], "handwriting")
    .to(
      welcomeLetters,
      {
        opacity: 1,
        y: 0,
        filter: "blur(0px)",
        rotation: 0,
        clipPath: "inset(0 0% 0 0)",
        duration: 0.5,
        stagger: (index) =>
          index * HANDWRITING_LETTER_STAGGER +
          HANDWRITING_TIMING_VARIATION[
            index % HANDWRITING_TIMING_VARIATION.length
          ],
        ease: "power2.out",
      },
      "handwriting"
    )
    .to(
      welcomeScreenAccent,
      {
        opacity: 1,
        scaleX: 1,
        duration: 0.65,
        ease: "power2.out",
      },
      "-=0.25"
    )
    .addLabel("paper-exit", "+=0.4")
    .call(playPaperExitSound, [], "paper-exit-=0.5")
    .to(
      welcomeScreenContent,
      {
        x: "-2vw",
        y: "-2vh",
        scale: 1.01,
        rotationX: 2,
        rotationY: -3,
        rotationZ: -2,
        duration: PAPER_EXIT_LIFT_DURATION,
        ease: "sine.inOut",
      },
      "paper-exit"
    )
    .to(welcomeScreenContent, {
      opacity: 0,
      x: "34vw",
      y: "-118vh",
      scale: 0.88,
      rotationX: 9,
      rotationY: -16,
      rotationZ: 12,
      duration: PAPER_EXIT_DURATION - PAPER_EXIT_LIFT_DURATION,
      ease: "power2.inOut",
    });
}

function playIntroAnimation() {
  const t1 = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  t1.timeScale(0.8);

  t1.to(plank1.scale, {
    x: 1,
    y: 1,
  })
    .to(
      plank2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      workBtn.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.6"
    )
    .to(
      aboutBtn.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.6"
    )
    .to(
      contactBtn.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.6"
    );

  const tFrames = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  tFrames.timeScale(0.8);

  tFrames
    .to(frame1.scale, {
      x: 1,
      y: 1,
      z: 1,
    })
    .to(
      frame2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      frame3.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    );

  const t2 = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  t2.timeScale(0.8);

  t2.to(boba.scale, {
    z: 1,
    y: 1,
    x: 1,
    delay: 0.4,
  })
    .to(
      github.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      youtube.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.6"
    );

  if (facebook) {
    t2.to(
      facebook.scale,
      {
        x: facebook.userData.initialScale.x,
        y: facebook.userData.initialScale.y,
        z: facebook.userData.initialScale.z,
        onComplete: activateFacebookHitbox,
      },
      "-=0.6"
    );
  }

  const tFlowers = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  tFlowers.timeScale(0.8);

  tFlowers
    .to(flower5.scale, {
      x: 1,
      y: 1,
      z: 1,
    })
    .to(
      flower4.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      flower3.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      flower2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      flower1.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    );

  const tBoxes = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  tBoxes.timeScale(0.8);

  tBoxes
    .to(box1.scale, {
      x: 1,
      y: 1,
      z: 1,
    })
    .to(
      box2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      box3.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    );

  const tLamp = gsap.timeline({
    defaults: {
      duration: 0.8,
      delay: 0.2,
      ease: "back.out(1.8)",
    },
  });
  tLamp.timeScale(0.8);

  tLamp.to(lamp.scale, {
    x: 1,
    y: 1,
    z: 1,
  });

  const tSlippers = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  tSlippers.timeScale(0.8);

  tSlippers
    .to(slippers1.scale, {
      x: 1,
      y: 1,
      z: 1,
      delay: 0.5,
    })
    .to(
      slippers2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    );

  const tEggs = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  tEggs.timeScale(0.8);

  tEggs
    .to(egg1.scale, {
      x: 1,
      y: 1,
      z: 1,
    })
    .to(
      egg2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    )
    .to(
      egg3.scale,
      {
        x: 1,
        y: 1,
        z: 1,
      },
      "-=0.5"
    );

  const tFish = gsap.timeline({
    defaults: {
      delay: 0.8,
      duration: 0.8,
      ease: "back.out(1.8)",
    },
  });
  tFish.timeScale(0.8);

  tFish.to(fish.scale, {
    x: 1,
    y: 1,
    z: 1,
  });

  const lettersTl = gsap.timeline({
    defaults: {
      duration: 0.8,
      ease: "back.out(1.7)",
    },
  });
  lettersTl.timeScale(0.8);

  lettersTl
    .to(letter1.position, {
      y: letter1.userData.initialPosition.y + 0.3,
      duration: 0.4,
      ease: "back.out(1.8)",
      delay: 0.25,
    })
    .to(
      letter1.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter1.position,
      {
        y: letter1.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter2.position,
      {
        y: letter2.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter2.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter2.position,
      {
        y: letter2.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter3.position,
      {
        y: letter3.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter3.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter3.position,
      {
        y: letter3.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter4.position,
      {
        y: letter4.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter4.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter4.position,
      {
        y: letter4.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter5.position,
      {
        y: letter5.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter5.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter5.position,
      {
        y: letter5.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter6.position,
      {
        y: letter6.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter6.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter6.position,
      {
        y: letter6.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter7.position,
      {
        y: letter7.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter7.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter7.position,
      {
        y: letter7.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    )

    .to(
      letter8.position,
      {
        y: letter8.userData.initialPosition.y + 0.3,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "-=0.5"
    )
    .to(
      letter8.scale,
      {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      "<"
    )
    .to(
      letter8.position,
      {
        y: letter8.userData.initialPosition.y,
        duration: 0.4,
        ease: "back.out(1.8)",
      },
      ">-0.2"
    );

  const pianoKeysTl = gsap.timeline({
    defaults: {
      duration: 0.4,
      ease: "back.out(1.7)",
      onComplete: () => {
        setTimeout(() => {
          createDelayedHitboxes();
        }, 1950);
      },
    },
  });
  pianoKeysTl.timeScale(1.2);

  const pianoKeys = [
    C1_Key,
    Cs1_Key,
    D1_Key,
    Ds1_Key,
    E1_Key,
    F1_Key,
    Fs1_Key,
    G1_Key,
    Gs1_Key,
    A1_Key,
    As1_Key,
    B1_Key,
    C2_Key,
    Cs2_Key,
    D2_Key,
    Ds2_Key,
    E2_Key,
    F2_Key,
    Fs2_Key,
    G2_Key,
    Gs2_Key,
    A2_Key,
    As2_Key,
    B2_Key,
  ];

  pianoKeys.forEach((key, index) => {
    pianoKeysTl
      .to(
        key.position,
        {
          y: key.userData.initialPosition.y + 0.2,
          duration: 0.4,
          ease: "back.out(1.8)",
        },
        index * 0.1
      )
      .to(
        key.scale,
        {
          x: 1,
          y: 1,
          z: 1,
          duration: 0.4,
          ease: "back.out(1.8)",
        },
        "<"
      )
      .to(
        key.position,
        {
          y: key.userData.initialPosition.y,
          duration: 0.4,
          ease: "back.out(1.8)",
        },
        ">-0.2"
      );
  });
}

/**  -------------------------- Loaders & Texture Preparations -------------------------- */
const textureLoader = new THREE.TextureLoader();

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("/draco/");

const loader = new GLTFLoader(manager);
loader.setDRACOLoader(dracoLoader);

const environmentMap = new THREE.CubeTextureLoader()
  .setPath("textures/skybox/")
  .load(["px.webp", "nx.webp", "py.webp", "ny.webp", "pz.webp", "nz.webp"]);

const textureMap = {
  First: {
    day: "/textures/room/day/first-texture-set-day.webp",
    night: "/textures/room/night/first-texture-set-night.webp",
  },
  Second: {
    day: "/textures/room/day/second-texture-set-day.webp",
    night: "/textures/room/night/second-texture-set-night.webp",
  },
  Third: {
    day: "/textures/room/day/third-texture-set-day.webp",
    night: "/textures/room/night/third-texture-set-night.webp",
  },
  Fourth: {
    day: "/textures/room/day/fourth-texture-set-day.webp",
    night: "/textures/room/night/fourth-texture-set-night.webp",
  },
};

const loadedTextures = {
  day: {},
  night: {},
};

Object.entries(textureMap).forEach(([key, paths]) => {
  // Load and configure day texture
  const dayTexture = textureLoader.load(paths.day);
  dayTexture.flipY = false;
  dayTexture.colorSpace = THREE.SRGBColorSpace;
  dayTexture.minFilter = THREE.LinearFilter;
  dayTexture.magFilter = THREE.LinearFilter;
  loadedTextures.day[key] = dayTexture;

  // Load and configure night texture
  const nightTexture = textureLoader.load(paths.night);
  nightTexture.flipY = false;
  nightTexture.colorSpace = THREE.SRGBColorSpace;
  nightTexture.minFilter = THREE.LinearFilter;
  nightTexture.magFilter = THREE.LinearFilter;
  loadedTextures.night[key] = nightTexture;
});

// Reuseable Materials
const glassMaterial = new THREE.MeshPhysicalMaterial({
  transmission: 1,
  opacity: 1,
  color: 0xfbfbfb,
  metalness: 0,
  roughness: 0,
  ior: 3,
  thickness: 0.01,
  specularIntensity: 1,
  envMap: environmentMap,
  envMapIntensity: 1,
  depthWrite: false,
  specularColor: 0xfbfbfb,
});

const whiteMaterial = new THREE.MeshBasicMaterial({
  color: 0xffffff,
});

const createMaterialForTextureSet = (textureSet) => {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      uDayTexture1: { value: loadedTextures.day.First },
      uNightTexture1: { value: loadedTextures.night.First },
      uDayTexture2: { value: loadedTextures.day.Second },
      uNightTexture2: { value: loadedTextures.night.Second },
      uDayTexture3: { value: loadedTextures.day.Third },
      uNightTexture3: { value: loadedTextures.night.Third },
      uDayTexture4: { value: loadedTextures.day.Fourth },
      uNightTexture4: { value: loadedTextures.night.Fourth },
      uMixRatio: { value: 0 },
      uTextureSet: { value: textureSet },
    },
    vertexShader: themeVertexShader,
    fragmentShader: themeFragmentShader,
  });

  Object.entries(material.uniforms).forEach(([key, uniform]) => {
    if (uniform.value instanceof THREE.Texture) {
      uniform.value.minFilter = THREE.LinearFilter;
      uniform.value.magFilter = THREE.LinearFilter;
    }
  });

  return material;
};

const roomMaterials = {
  First: createMaterialForTextureSet(1),
  Second: createMaterialForTextureSet(2),
  Third: createMaterialForTextureSet(3),
  Fourth: createMaterialForTextureSet(4),
};

const outsideTreeMaterials = [];

function createOutsideTreeMaterial(sourceMaterial) {
  const dayColor =
    sourceMaterial.color?.clone() ?? new THREE.Color(0xffffff);
  const isLeaves = sourceMaterial.name === "Tree_Green";
  const material = new THREE.ShaderMaterial({
    uniforms: {
      uDayColor: { value: dayColor },
      uNightColor: { value: dayColor.clone().multiplyScalar(0.14) },
      uThemeMix: { value: 0 },
      uLightDirectionWorld: {
        value: new THREE.Vector3(-0.42, 0.82, 0.39).normalize(),
      },
      uSkyTint: { value: new THREE.Color("#f1e4dc") },
      uGroundTint: { value: new THREE.Color("#777986") },
      uMorningSpecularColor: { value: new THREE.Color("#ffd3a1") },
      uSpecularStrength: { value: isLeaves ? 0.18 : 0.1 },
      uSpecularPower: { value: isLeaves ? 18 : 28 },
      uOpacity: { value: sourceMaterial.opacity },
    },
    vertexShader: treeVertexShader,
    fragmentShader: treeFragmentShader,
    transparent: sourceMaterial.transparent,
    side: sourceMaterial.side,
    depthWrite: sourceMaterial.depthWrite,
    depthTest: sourceMaterial.depthTest,
    toneMapped: sourceMaterial.toneMapped,
  });

  material.name = sourceMaterial.name;
  outsideTreeMaterials.push(material);

  return material;
}

// Smoke Shader setup
const smokeGeometry = new THREE.PlaneGeometry(1, 1, 16, 64);
smokeGeometry.translate(0, 0.5, 0);
smokeGeometry.scale(0.33, 1, 0.33);

const perlinTexture = textureLoader.load("/shaders/perlin.png");
perlinTexture.wrapS = THREE.RepeatWrapping;
perlinTexture.wrapT = THREE.RepeatWrapping;

const smokeMaterial = new THREE.ShaderMaterial({
  vertexShader: smokeVertexShader,
  fragmentShader: smokeFragmentShader,
  uniforms: {
    uTime: new THREE.Uniform(0),
    uPerlinTexture: new THREE.Uniform(perlinTexture),
  },
  side: THREE.DoubleSide,
  transparent: true,
  depthWrite: false,
});

const smoke = new THREE.Mesh(smokeGeometry, smokeMaterial);
smoke.position.y = 1.83;
scene.add(smoke);

const videoElement = document.createElement("video");
videoElement.src = "/textures/video/screen.mp4";
videoElement.loop = true;
videoElement.muted = true;
videoElement.playsInline = true;
videoElement.autoplay = true;
videoElement.play();

const videoTexture = new THREE.VideoTexture(videoElement);
videoTexture.colorSpace = THREE.SRGBColorSpace;
videoTexture.flipY = false;

/**  -------------------------- Model and Mesh Setup -------------------------- */

// LOL DO NOT DO THIS USE A FUNCTION TO AUTOMATE THIS PROCESS HAHAHAAHAHAHAHAHAHA
let fish;
let coffeePosition;
let hourHand;
let minuteHand;
let chairTop;
const xAxisFans = [];
const yAxisFans = [];
let plank1,
  plank2,
  workBtn,
  aboutBtn,
  contactBtn,
  boba,
  github,
  youtube,
  twitter;

let facebook;
let facebookHitbox;
let isFacebookHitboxActive = false;

let letter1, letter2, letter3, letter4, letter5, letter6, letter7, letter8;

let C1_Key,
  Cs1_Key,
  D1_Key,
  Ds1_Key,
  E1_Key,
  F1_Key,
  Fs1_Key,
  G1_Key,
  Gs1_Key,
  A1_Key,
  As1_Key,
  B1_Key;
let C2_Key,
  Cs2_Key,
  D2_Key,
  Ds2_Key,
  E2_Key,
  F2_Key,
  Fs2_Key,
  G2_Key,
  Gs2_Key,
  A2_Key,
  As2_Key,
  B2_Key;

let flower1, flower2, flower3, flower4, flower5;

let box1, box2, box3;

let lamp;

let slippers1, slippers2;

let egg1, egg2, egg3;

let frame1, frame2, frame3;

const useOriginalMeshObjects = ["Bulb", "Cactus", "Kirby"];

const objectsNeedingHitboxes = [];

const objectsWithIntroAnimations = [
  "Hanging_Plank_1",
  "Hanging_Plank_2",
  "My_Work_Button",
  "About_Button",
  "Contact_Button",
  "Boba",
  "GitHub",
  "YouTube",
  "Twitter",
  "Name_Letter_1",
  "Name_Letter_2",
  "Name_Letter_3",
  "Name_Letter_4",
  "Name_Letter_5",
  "Name_Letter_6",
  "Name_Letter_7",
  "Name_Letter_8",
  "Flower_1",
  "Flower_2",
  "Flower_3",
  "Flower_4",
  "Flower_5",
  "Box_1",
  "Box_2",
  "Box_3",
  "Lamp",
  "Slipper_1",
  "Slipper_2",
  "Fish_Fourth",
  "Egg_1",
  "Egg_2",
  "Egg_3",
  "Frame_1",
  "Frame_2",
  "Frame_3",
  "C1_Key",
  "C#1_Key",
  "D1_Key",
  "D#1_Key",
  "E1_Key",
  "F1_Key",
  "F#1_Key",
  "G1_Key",
  "G#1_Key",
  "A1_Key",
  "A#1_Key",
  "B1_Key",
  "C2_Key",
  "C#2_Key",
  "D2_Key",
  "D#2_Key",
  "E2_Key",
  "F2_Key",
  "F#2_Key",
  "G2_Key",
  "G#2_Key",
  "A2_Key",
  "A#2_Key",
  "B2_Key",
];

function hasIntroAnimation(objectName) {
  return objectsWithIntroAnimations.some((animatedName) =>
    objectName.includes(animatedName)
  );
}

loader.load("/models/room-main.glb", (glb) => {
  glb.scene.traverse((child) => {
    if (child.isMesh) {
      if (child.name.includes("Twitter")) {
        child.visible = false;
      }

      if (child.name.includes("Fish_Fourth")) {
        fish = child;
        child.position.x += 0.04;
        child.position.z -= 0.03;
        child.userData.initialPosition = new THREE.Vector3().copy(
          child.position
        );
      }
      if (child.name.includes("Chair_Top")) {
        chairTop = child;
        child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
      }

      if (child.name.includes("Hour_Hand")) {
        hourHand = child;
        child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
      }

      if (child.name.includes("Minute_Hand")) {
        minuteHand = child;
        child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
      }

      if (child.name.includes("Coffee")) {
        coffeePosition = child.position.clone();
      }

      if (child.name.includes("Hover") || child.name.includes("Key")) {
        child.userData.initialScale = new THREE.Vector3().copy(child.scale);
        child.userData.initialPosition = new THREE.Vector3().copy(
          child.position
        );
        child.userData.initialRotation = new THREE.Euler().copy(child.rotation);
      }

      // LOL DO NOT DO THIS USE A FUNCTION TO AUTOMATE THIS PROCESS HAHAHAAHAHAHAHAHAHA
      if (child.name.includes("Hanging_Plank_1")) {
        plank1 = child;
        child.scale.set(0, 0, 1);
      } else if (child.name.includes("Hanging_Plank_2")) {
        plank2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("My_Work_Button")) {
        workBtn = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("About_Button")) {
        aboutBtn = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Contact_Button")) {
        contactBtn = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Boba")) {
        boba = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("GitHub")) {
        github = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("YouTube")) {
        youtube = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Twitter")) {
        twitter = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_1")) {
        letter1 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_2")) {
        letter2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_3")) {
        letter3 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_4")) {
        letter4 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_5")) {
        letter5 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_6")) {
        letter6 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_7")) {
        letter7 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Name_Letter_8")) {
        letter8 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Flower_1")) {
        flower1 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Flower_2")) {
        flower2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Flower_3")) {
        flower3 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Flower_4")) {
        flower4 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Flower_5")) {
        flower5 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Box_1")) {
        box1 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Box_2")) {
        box2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Box_3")) {
        box3 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Lamp")) {
        lamp = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Slipper_1")) {
        slippers1 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Slipper_2")) {
        slippers2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Fish_Fourth")) {
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Egg_1")) {
        egg1 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Egg_2")) {
        egg2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Egg_3")) {
        egg3 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Frame_1")) {
        frame1 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Frame_2")) {
        frame2 = child;
        child.scale.set(0, 0, 0);
      } else if (child.name.includes("Frame_3")) {
        frame3 = child;
        child.scale.set(0, 0, 0);
      }
      Object.keys(pianoKeyMap).forEach((keyName) => {
        if (child.name.includes(keyName)) {
          const varName = keyName.replace("#", "s").split("_")[0] + "_Key";
          eval(`${varName} = child`);
          child.scale.set(0, 0, 0);
          child.userData.initialPosition = new THREE.Vector3().copy(
            child.position
          );
        }
      });

      if (child.name.includes("Water")) {
        child.material = new THREE.MeshBasicMaterial({
          color: 0x558bc8,
          transparent: true,
          opacity: 0.4,
          depthWrite: false,
        });
      } else if (child.name.includes("Glass")) {
        child.material = glassMaterial;
      } else if (child.name.includes("Bubble")) {
        child.material = whiteMaterial;
      } else if (child.name.includes("Screen")) {
        child.material = new THREE.MeshBasicMaterial({
          map: videoTexture,
          transparent: true,
          opacity: 0.9,
        });
      } else {
        Object.keys(textureMap).forEach((key) => {
          if (child.name.includes(key)) {
            child.material = roomMaterials[key];

            if (child.name.includes("Fan")) {
              if (
                child.name.includes("Fan_2") ||
                child.name.includes("Fan_4")
              ) {
                xAxisFans.push(child);
              } else {
                yAxisFans.push(child);
              }
            }
          }
        });
      }

      if (
        child.name.includes("Raycaster") &&
        !child.name.includes("Twitter")
      ) {
        if (hasIntroAnimation(child.name)) {
          // Create a hitbox for object after intro is done playing,
          // Set an original scale first for the hitbox
          child.userData.originalScale = new THREE.Vector3(1, 1, 1);

          objectsNeedingHitboxes.push(child);
        } else {
          // Create immediate hitboxes/meshes for objects that DON'T have an intro animation
          const raycastObject = createStaticHitbox(child);

          if (raycastObject !== child) {
            scene.add(raycastObject);
          }

          raycasterObjects.push(raycastObject);
          hitboxToObjectMap.set(raycastObject, child);
        }
      }
    }
  });

  if (coffeePosition) {
    smoke.position.set(
      coffeePosition.x,
      coffeePosition.y + 0.2,
      coffeePosition.z
    );
  }

  scene.add(glb.scene);
});

loader.load("/models/outside-tree.glb", (glb) => {
  glb.scene.traverse((child) => {
    if (!child.isMesh) return;

    child.material = Array.isArray(child.material)
      ? child.material.map(createOutsideTreeMaterial)
      : createOutsideTreeMaterial(child.material);
  });

  scene.add(glb.scene);
});

/**  -------------------------- Raycaster setup -------------------------- */

const raycasterObjects = [];
let currentIntersects = [];
let currentHoveredObject = null;

const socialLinks = {
  GitHub: "https://github.com/hiepdeptrai321",
  Facebook: "https://www.facebook.com/hiepdeptrai321",
};

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

const hitboxToObjectMap = new Map();

function shouldUseOriginalMesh(objectName) {
  return useOriginalMeshObjects.some((meshName) =>
    objectName.includes(meshName)
  );
}

function createStaticHitbox(originalObject) {
  // Check if we should use original mesh
  if (shouldUseOriginalMesh(originalObject.name)) {
    if (!originalObject.userData.initialScale) {
      originalObject.userData.initialScale = new THREE.Vector3().copy(
        originalObject.scale
      );
    }
    if (!originalObject.userData.initialPosition) {
      originalObject.userData.initialPosition = new THREE.Vector3().copy(
        originalObject.position
      );
    }
    if (!originalObject.userData.initialRotation) {
      originalObject.userData.initialRotation = new THREE.Euler().copy(
        originalObject.rotation
      );
    }

    originalObject.userData.originalObject = originalObject;
    return originalObject;
  }

  if (!originalObject.userData.initialScale) {
    originalObject.userData.initialScale = new THREE.Vector3().copy(
      originalObject.scale
    );
  }
  if (!originalObject.userData.initialPosition) {
    originalObject.userData.initialPosition = new THREE.Vector3().copy(
      originalObject.position
    );
  }
  if (!originalObject.userData.initialRotation) {
    originalObject.userData.initialRotation = new THREE.Euler().copy(
      originalObject.rotation
    );
  }

  const currentScale = originalObject.scale.clone();
  const hasZeroScale =
    currentScale.x === 0 || currentScale.y === 0 || currentScale.z === 0;

  if (hasZeroScale && originalObject.userData.originalScale) {
    originalObject.scale.copy(originalObject.userData.originalScale);
  }

  const box = new THREE.Box3().setFromObject(originalObject);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  if (hasZeroScale) {
    originalObject.scale.copy(currentScale);
  }

  let hitboxGeometry;
  let sizeMultiplier = { x: 1.1, y: 1.75, z: 1.1 };

  hitboxGeometry = new THREE.BoxGeometry(
    size.x * sizeMultiplier.x,
    size.y * sizeMultiplier.y,
    size.z * sizeMultiplier.z
  );

  const hitboxMaterial = new THREE.MeshBasicMaterial({
    transparent: true,
    opacity: 0,
    visible: false,
  });

  const hitbox = new THREE.Mesh(hitboxGeometry, hitboxMaterial);
  hitbox.position.copy(center);
  hitbox.name = originalObject.name + "_Hitbox";
  hitbox.userData.originalObject = originalObject;

  if (originalObject.name.includes("Headphones")) {
    hitbox.rotation.x = 0;
    hitbox.rotation.y = Math.PI / 4;
    hitbox.rotation.z = 0;
  }

  return hitbox;
}

function createDelayedHitboxes() {
  objectsNeedingHitboxes.forEach((child) => {
    const raycastObject = createStaticHitbox(child);

    if (raycastObject !== child) {
      scene.add(raycastObject);
    }

    raycasterObjects.push(raycastObject);
    hitboxToObjectMap.set(raycastObject, child);
  });

  objectsNeedingHitboxes.length = 0;
}

function activateFacebookHitbox() {
  if (!facebookHitbox || isFacebookHitboxActive) return;

  raycasterObjects.push(facebookHitbox);
  isFacebookHitboxActive = true;
}

const FACEBOOK_CARD_COLORS = {
  blue: {
    rest: new THREE.Color("#455a86"),
    hover: new THREE.Color("#576f9e"),
  },
  white: {
    rest: new THREE.Color("#ded8d4"),
    hover: new THREE.Color("#f0e8e3"),
  },
};

function createUnlitMaterial(material) {
  const sourceColor = material.color ?? new THREE.Color(0xffffff);
  const isFacebookBlue =
    material.name === "Material.001" ||
    (material.name !== "Material.f" &&
      sourceColor.b > sourceColor.r * 1.5 &&
      sourceColor.b > sourceColor.g * 1.5);
  const palette = isFacebookBlue
    ? FACEBOOK_CARD_COLORS.blue
    : FACEBOOK_CARD_COLORS.white;
  const unlitMaterial = new THREE.MeshBasicMaterial({
    color: palette.rest,
    map: material.map ?? null,
    transparent: material.transparent,
    opacity: material.opacity,
    alphaTest: material.alphaTest,
    side: material.side,
    depthWrite: material.depthWrite,
    vertexColors: material.vertexColors,
  });

  unlitMaterial.name = material.name;
  unlitMaterial.userData.facebookRole = isFacebookBlue ? "blue" : "white";
  unlitMaterial.userData.facebookRestColor = palette.rest.clone();
  unlitMaterial.userData.facebookHoverColor = palette.hover.clone();

  return unlitMaterial;
}

function animateFacebookMaterials(object, isHovering) {
  object.traverse((child) => {
    if (!child.isMesh) return;

    const materials = Array.isArray(child.material)
      ? child.material
      : [child.material];

    materials.forEach((material) => {
      const targetColor = isHovering
        ? material.userData.facebookHoverColor
        : material.userData.facebookRestColor;

      if (!targetColor) return;

      gsap.killTweensOf(material.color);
      gsap.to(material.color, {
        r: targetColor.r,
        g: targetColor.g,
        b: targetColor.b,
        duration: isHovering ? 0.25 : 0.3,
        ease: "power2.out",
      });
    });
  });
}

function createBottomCenterAnimationPivot(object) {
  const parent = object.parent;
  if (!parent) return object;

  object.updateWorldMatrix(true, true);

  const objectWorldInverse = object.matrixWorld.clone().invert();
  const localBounds = new THREE.Box3().makeEmpty();

  object.traverse((child) => {
    if (!child.isMesh || !child.geometry) return;

    if (!child.geometry.boundingBox) {
      child.geometry.computeBoundingBox();
    }

    const childToObject = new THREE.Matrix4().multiplyMatrices(
      objectWorldInverse,
      child.matrixWorld
    );
    const childBounds = child.geometry.boundingBox
      .clone()
      .applyMatrix4(childToObject);

    localBounds.union(childBounds);
  });

  if (localBounds.isEmpty()) return object;

  const anchor = localBounds.getCenter(new THREE.Vector3());
  anchor.z = localBounds.max.z;

  const pivotPosition = anchor
    .clone()
    .multiply(object.scale)
    .applyQuaternion(object.quaternion)
    .add(object.position);
  const originalName = object.name;
  const pivot = new THREE.Group();

  pivot.name = originalName;
  pivot.position.copy(pivotPosition);
  pivot.quaternion.copy(object.quaternion);
  pivot.scale.copy(object.scale);

  parent.add(pivot);
  pivot.add(object);

  object.name = `${originalName}_Visual`;
  object.position.copy(anchor).multiplyScalar(-1);
  object.quaternion.identity();
  object.scale.set(1, 1, 1);

  return pivot;
}

function addStandaloneInteractiveModel(modelUrl) {
  loader.load(modelUrl, (glb) => {
    const interactiveObjects = [];

    glb.scene.traverse((child) => {
      if (child.isMesh) {
        child.material = Array.isArray(child.material)
          ? child.material.map(createUnlitMaterial)
          : createUnlitMaterial(child.material);
      }

      if (
        child.name.includes("Raycaster") &&
        !child.parent?.name.includes("Raycaster")
      ) {
        interactiveObjects.push(child);
      }
    });

    interactiveObjects.forEach((object) => {
      const isFacebook = object.name.includes("Facebook");
      const animationObject = isFacebook
        ? createBottomCenterAnimationPivot(object)
        : object;

      if (animationObject.name.includes("Hover")) {
        animationObject.userData.initialScale = animationObject.scale.clone();
        animationObject.userData.initialPosition =
          animationObject.position.clone();
        animationObject.userData.initialRotation =
          animationObject.rotation.clone();
      }

      const raycastObject = createStaticHitbox(animationObject);

      if (raycastObject !== animationObject) {
        scene.add(raycastObject);
      }

      hitboxToObjectMap.set(raycastObject, animationObject);

      if (isFacebook) {
        facebook = animationObject;
        facebookHitbox = raycastObject;
        facebook.scale.set(0, 0, 0);
        return;
      }

      raycasterObjects.push(raycastObject);
    });

    scene.add(glb.scene);
  });
}

addStandaloneInteractiveModel("/models/facebook-card.glb");

function isStoryTriggerObject(objectName) {
  return (
    objectName.includes("Story_English") ||
    objectName.includes("Headphones") ||
    objectName.includes("Microphone")
  );
}

function handleRaycasterInteraction() {
  if (currentIntersects.length > 0) {
    const hitbox = currentIntersects[0].object;
    const object = hitboxToObjectMap.get(hitbox);

    if (object.name.includes("Button")) {
      buttonSounds.click.play();
    }

    Object.entries(pianoKeyMap).forEach(([keyName, soundKey]) => {
      if (object.name.includes(keyName)) {
        if (pianoDebounceTimer) {
          clearTimeout(pianoDebounceTimer);
        }

        fadeOutBackgroundMusic();

        pianoSounds[soundKey].play();

        pianoDebounceTimer = setTimeout(() => {
          fadeInBackgroundMusic();
        }, PIANO_TIMEOUT);

        gsap.to(object.rotation, {
          x: object.userData.initialRotation.x + Math.PI / 42,
          duration: 0.4,
          ease: "back.out(2)",
          onComplete: () => {
            gsap.to(object.rotation, {
              x: object.userData.initialRotation.x,
              duration: 0.25,
              ease: "back.out(2)",
            });
          },
        });
      }
    });

    Object.entries(socialLinks).forEach(([key, url]) => {
      if (object.name.includes(key)) {
        window.open(url, "_blank", "noopener,noreferrer");
      }
    });

    if (isStoryTriggerObject(object.name)) {
      storyModal.open("storyEnglish");
      return;
    }

    if (object.name.includes("Work_Button")) {
      showModal(modals.work);
    } else if (object.name.includes("About_Button")) {
      showModal(modals.about);
    } else if (object.name.includes("Contact_Button")) {
      showModal(modals.contact);
    }
  }
}

function playHoverAnimation(objectHitbox, isHovering) {
  let scale = 1.4;
  const object = hitboxToObjectMap.get(objectHitbox);

  if (object.name.includes("Facebook")) {
    animateFacebookMaterials(object, isHovering);
  }

  gsap.killTweensOf(object.scale);
  gsap.killTweensOf(object.rotation);
  gsap.killTweensOf(object.position);

  if (object.name.includes("Coffee")) {
    gsap.killTweensOf(smoke.scale);
    if (isHovering) {
      gsap.to(smoke.scale, {
        x: 1.4,
        y: 1.4,
        z: 1.4,
        duration: 0.5,
        ease: "back.out(2)",
      });
    } else {
      gsap.to(smoke.scale, {
        x: 1,
        y: 1,
        z: 1,
        duration: 0.3,
        ease: "back.out(2)",
      });
    }
  }

  if (object.name.includes("Fish")) {
    scale = 1.2;
  }

  if (isHovering) {
    // Scale animation for all objects
    gsap.to(object.scale, {
      x: object.userData.initialScale.x * scale,
      y: object.userData.initialScale.y * scale,
      z: object.userData.initialScale.z * scale,
      duration: 0.5,
      ease: "back.out(2)",
    });

    if (object.name.includes("About_Button")) {
      gsap.to(object.rotation, {
        x: object.userData.initialRotation.x - Math.PI / 10,
        duration: 0.5,
        ease: "back.out(2)",
      });
    } else if (
      object.name.includes("Contact_Button") ||
      object.name.includes("My_Work_Button") ||
      object.name.includes("GitHub") ||
      object.name.includes("Facebook") ||
      object.name.includes("YouTube") ||
      object.name.includes("Twitter")
    ) {
      gsap.to(object.rotation, {
        x: object.userData.initialRotation.x + Math.PI / 10,
        duration: 0.5,
        ease: "back.out(2)",
      });
    }

    if (object.name.includes("Boba") || object.name.includes("Name_Letter")) {
      gsap.to(object.position, {
        y: object.userData.initialPosition.y + 0.2,
        duration: 0.5,
        ease: "back.out(2)",
      });
    }
  } else {
    // Reset scale for all objects
    gsap.to(object.scale, {
      x: object.userData.initialScale.x,
      y: object.userData.initialScale.y,
      z: object.userData.initialScale.z,
      duration: 0.3,
      ease: "back.out(2)",
    });

    if (
      object.name.includes("About_Button") ||
      object.name.includes("Contact_Button") ||
      object.name.includes("My_Work_Button") ||
      object.name.includes("GitHub") ||
      object.name.includes("Facebook") ||
      object.name.includes("YouTube") ||
      object.name.includes("Twitter")
    ) {
      gsap.to(object.rotation, {
        x: object.userData.initialRotation.x,
        duration: 0.3,
        ease: "back.out(2)",
      });
    }

    if (object.name.includes("Boba") || object.name.includes("Name_Letter")) {
      gsap.to(object.position, {
        y: object.userData.initialPosition.y,
        duration: 0.3,
        ease: "back.out(2)",
      });
    }
  }
}

canvas.addEventListener("mousemove", (e) => {
  hasTouchHappened = false;
  pointer.x = (e.clientX / sizes.width) * 2 - 1;
  pointer.y = -(e.clientY / sizes.height) * 2 + 1;
});

canvas.addEventListener(
  "touchstart",
  (e) => {
    if (isModalOpen) return;
    e.preventDefault();
    const touch = e.touches[0];
    touchStartPosition = { x: touch.clientX, y: touch.clientY };
    hasTouchMoved = false;
    pointer.x = (touch.clientX / sizes.width) * 2 - 1;
    pointer.y = -(touch.clientY / sizes.height) * 2 + 1;
  },
  { passive: false }
);

canvas.addEventListener(
  "touchmove",
  (e) => {
    if (isModalOpen || !touchStartPosition) return;
    const touch = e.touches[0];
    const moveX = Math.abs(touch.clientX - touchStartPosition.x);
    const moveY = Math.abs(touch.clientY - touchStartPosition.y);

    if (moveX > TOUCH_MOVE_THRESHOLD || moveY > TOUCH_MOVE_THRESHOLD) {
      hasTouchMoved = true;
    }
  },
  { passive: true }
);

canvas.addEventListener(
  "touchend",
  (e) => {
    if (isModalOpen) return;

    const shouldIgnoreTap = hasTouchMoved || !touchStartPosition;
    touchStartPosition = null;
    hasTouchMoved = false;

    if (shouldIgnoreTap) return;

    e.preventDefault();
    handleRaycasterInteraction();
  },
  { passive: false }
);

canvas.addEventListener("click", handleRaycasterInteraction);
window.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;

  const modal = document.querySelector('.modal[style*="display: block"]');
  if (modal) hideModal(modal);
});

// Other Event Listeners
const themeToggleButton = document.querySelector(".theme-toggle-button");
const audioControls = document.querySelector(".audio-controls");
const muteToggleButton = document.querySelector(".mute-toggle-button");
const volumeSlider = document.querySelector(".volume-slider");
const sunSvg = document.querySelector(".sun-svg");
const moonSvg = document.querySelector(".moon-svg");
const soundOffSvg = document.querySelector(".sound-off-svg");
const soundOnSvg = document.querySelector(".sound-on-svg");
const roomHero = document.querySelector(".room-hero");
const backToRoomLink = document.querySelector(".back-to-room-link");

const setBackToRoomVisibility = (shouldShow) => {
  backToRoomLink.classList.toggle("is-visible", shouldShow);
  backToRoomLink.setAttribute("aria-hidden", String(!shouldShow));

  if (shouldShow) {
    backToRoomLink.removeAttribute("tabindex");
  } else {
    backToRoomLink.setAttribute("tabindex", "-1");
  }
};

const roomVisibilityObserver = new IntersectionObserver(
  ([entry]) => {
    const hasPassedRoom =
      !entry.isIntersecting && entry.boundingClientRect.bottom <= 0;
    setBackToRoomVisibility(hasPassedRoom);
  },
  { threshold: 0 }
);

roomVisibilityObserver.observe(roomHero);

const updateSoundIcon = () => {
  soundOnSvg.style.display = isMuted ? "none" : "block";
  soundOffSvg.style.display = isMuted ? "block" : "none";
};

const updateMuteState = (muted) => {
  Howler.mute(muted);
  updateSoundIcon();
  updateSoundControlLabels();
};

const handleMuteToggle = (e) => {
  e.preventDefault();

  if (isMuted && currentVolume === 0) {
    currentVolume = lastAudibleVolume;
    Howler.volume(currentVolume);
    volumeSlider.value = currentVolume;
  }

  isMuted = !isMuted;
  updateMuteState(isMuted);
  buttonSounds.click.play();

  if (!isMuted && hasEnteredRoom && !backgroundMusic.playing()) {
    backgroundMusic.play();
  }

  gsap.to(muteToggleButton, {
    rotate: -12,
    scale: 1.15,
    duration: 0.2,
    ease: "back.out(2)",
    onStart: () => {
      gsap.to(muteToggleButton, {
        rotate: 0,
        scale: 1,
        duration: 0.25,
        ease: "back.out(2)",
        onComplete: () => {
          gsap.set(muteToggleButton, {
            clearProps: "all",
          });
        },
      });
    },
  });
};

muteToggleButton.addEventListener(
  "click",
  (e) => {
    if (hasTouchHappened) return;
    handleMuteToggle(e);
  },
  { passive: false }
);

volumeSlider.addEventListener("input", (event) => {
  currentVolume = Number(event.target.value);
  Howler.volume(currentVolume);

  if (currentVolume > 0) {
    lastAudibleVolume = currentVolume;
    isMuted = false;
    Howler.mute(false);

    if (hasEnteredRoom && !backgroundMusic.playing()) {
      backgroundMusic.play();
    }
  } else {
    isMuted = true;
    Howler.mute(true);
  }

  updateSoundIcon();
  updateSoundControlLabels();
});

muteToggleButton.addEventListener(
  "touchend",
  (e) => {
    hasTouchHappened = true;
    audioControls.classList.toggle("is-volume-open");
    handleMuteToggle(e);
  },
  { passive: false }
);

document.addEventListener("pointerdown", (event) => {
  if (
    event.pointerType !== "mouse" &&
    !audioControls.contains(event.target)
  ) {
    audioControls.classList.remove("is-volume-open");
  }
});

// Themeing stuff
const toggleFavicons = () => {
  const isDark = document.body.classList.contains("dark-theme");
  const theme = isDark ? "light" : "dark";

  document.querySelector(
    'link[sizes="96x96"]'
  ).href = `media/${theme}-favicon/favicon-96x96.png`;
  document.querySelector(
    'link[type="image/svg+xml"]'
  ).href = `/media/${theme}-favicon/favicon.svg`;
  document.querySelector(
    'link[rel="shortcut icon"]'
  ).href = `media/${theme}-favicon/favicon.ico`;
  document.querySelector(
    'link[rel="apple-touch-icon"]'
  ).href = `media/${theme}-favicon/apple-touch-icon.png`;
  document.querySelector(
    'link[rel="manifest"]'
  ).href = `media/${theme}-favicon/site.webmanifest`;
};

let isNightMode = false;

const handleThemeToggle = (e) => {
  e.preventDefault();
  toggleFavicons();

  const isDark = document.body.classList.contains("dark-theme");
  document.body.classList.remove(isDark ? "dark-theme" : "light-theme");
  document.body.classList.add(isDark ? "light-theme" : "dark-theme");

  isNightMode = !isNightMode;
  buttonSounds.click.play();

  gsap.to(themeToggleButton, {
    rotate: 45,
    scale: 5,
    duration: 0.5,
    ease: "back.out(2)",
    onStart: () => {
      if (isNightMode) {
        sunSvg.style.display = "none";
        moonSvg.style.display = "block";
      } else {
        moonSvg.style.display = "none";
        sunSvg.style.display = "block";
      }

      gsap.to(themeToggleButton, {
        rotate: 0,
        scale: 1,
        duration: 0.5,
        ease: "back.out(2)",
        onComplete: () => {
          gsap.set(themeToggleButton, {
            clearProps: "all",
          });
        },
      });
    },
  });

  Object.values(roomMaterials).forEach((material) => {
    gsap.to(material.uniforms.uMixRatio, {
      value: isNightMode ? 1 : 0,
      duration: 1.5,
      ease: "power2.inOut",
    });
  });

  outsideTreeMaterials.forEach((material) => {
    gsap.to(material.uniforms.uThemeMix, {
      value: isNightMode ? 1 : 0,
      duration: 1.5,
      ease: "power2.inOut",
    });
  });
};

// Click event listener
themeToggleButton.addEventListener(
  "click",
  (e) => {
    if (hasTouchHappened) return;
    handleThemeToggle(e);
  },
  { passive: false }
);

themeToggleButton.addEventListener(
  "touchend",
  (e) => {
    hasTouchHappened = true;
    handleThemeToggle(e);
  },
  { passive: false }
);

/**  -------------------------- Render and Animations Stuff -------------------------- */
const clock = new THREE.Clock();

const updateClockHands = () => {
  if (!hourHand || !minuteHand) return;

  const now = new Date();
  const hours = now.getHours() % 12;
  const minutes = now.getMinutes();
  const seconds = now.getSeconds();

  const minuteAngle = (minutes + seconds / 60) * ((Math.PI * 2) / 60);

  const hourAngle = (hours + minutes / 60) * ((Math.PI * 2) / 12);

  minuteHand.rotation.x = -minuteAngle;
  hourHand.rotation.x = -hourAngle;
};

const render = (timestamp) => {
  const elapsedTime = clock.getElapsedTime();

  // Update Shader Univform
  smokeMaterial.uniforms.uTime.value = elapsedTime;

  //Update Orbit Controls
  controls.update();

  // Update Clock hand rotation
  updateClockHands();

  // Fan rotate animation
  xAxisFans.forEach((fan) => {
    fan.rotation.x -= 0.04;
  });

  yAxisFans.forEach((fan) => {
    fan.rotation.y -= 0.04;
  });

  // Chair rotate animation
  if (chairTop) {
    const time = timestamp * 0.001;
    const baseAmplitude = Math.PI / 8;

    const rotationOffset =
      baseAmplitude *
      Math.sin(time * 0.5) *
      (1 - Math.abs(Math.sin(time * 0.5)) * 0.3);

    chairTop.rotation.y = chairTop.userData.initialRotation.y + rotationOffset;
  }

  // Fish up and down animation
  if (fish) {
    const time = timestamp * 0.0015;
    const amplitude = 0.12;
    const position =
      amplitude * Math.sin(time) * (1 - Math.abs(Math.sin(time)) * 0.1);
    fish.position.y = fish.userData.initialPosition.y + position;
  }

  // Raycaster
  if (!isModalOpen) {
    raycaster.setFromCamera(pointer, camera);

    // Get all the objects the raycaster is currently shooting through / intersecting with
    currentIntersects = raycaster.intersectObjects(raycasterObjects);

    for (let i = 0; i < currentIntersects.length; i++) {}

    if (currentIntersects.length > 0) {
      const currentIntersectObject = currentIntersects[0].object;

      if (currentIntersectObject.name.includes("Hover")) {
        if (currentIntersectObject !== currentHoveredObject) {
          if (currentHoveredObject) {
            playHoverAnimation(currentHoveredObject, false);
          }

          currentHoveredObject = currentIntersectObject;
          playHoverAnimation(currentIntersectObject, true);
        }
      }

      if (currentIntersectObject.name.includes("Pointer")) {
        document.body.style.cursor = "pointer";
      } else {
        document.body.style.cursor = "default";
      }
    } else {
      if (currentHoveredObject) {
        playHoverAnimation(currentHoveredObject, false);
        currentHoveredObject = null;
      }
      document.body.style.cursor = "default";
    }
  }

  renderer.render(scene, camera);

  window.requestAnimationFrame(render);
};

render();

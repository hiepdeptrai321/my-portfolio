const DAY_WEATHERS = ["sunny", "rainy"];
const MAX_FRAME_DELTA = 0.04;

const clamp = (value, minimum, maximum) =>
  Math.min(Math.max(value, minimum), maximum);

const randomBetween = (minimum, maximum) =>
  minimum + Math.random() * (maximum - minimum);

export class AmbientBackground {
  constructor({ canvas, root = document.body }) {
    this.canvas = canvas;
    this.root = root;
    this.context = canvas?.getContext("2d", { alpha: true });

    if (!this.context) return;

    this.width = 0;
    this.height = 0;
    this.pixelRatio = 1;
    this.theme = null;
    this.dayWeather = null;
    this.animationFrameId = null;
    this.resizeFrameId = null;
    this.previousFrameTime = performance.now();
    this.nextShootingStarTime = 0;
    this.stars = [];
    this.shootingStars = [];
    this.clouds = [];
    this.sunMotes = [];
    this.rainDrops = [];

    this.reducedMotionQuery = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    );

    this.renderFrame = this.renderFrame.bind(this);
    this.handleResize = this.handleResize.bind(this);
    this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    this.handleReducedMotionChange =
      this.handleReducedMotionChange.bind(this);

    this.themeObserver = new MutationObserver(() => this.syncTheme());
    this.themeObserver.observe(this.root, {
      attributes: true,
      attributeFilter: ["class"],
    });

    window.addEventListener("resize", this.handleResize, { passive: true });
    document.addEventListener(
      "visibilitychange",
      this.handleVisibilityChange
    );

    if (this.reducedMotionQuery.addEventListener) {
      this.reducedMotionQuery.addEventListener(
        "change",
        this.handleReducedMotionChange
      );
    } else {
      this.reducedMotionQuery.addListener(this.handleReducedMotionChange);
    }

    this.resizeCanvas();
    this.syncTheme(true);
  }

  chooseDayWeather() {
    this.dayWeather =
      DAY_WEATHERS[Math.floor(Math.random() * DAY_WEATHERS.length)];
    this.root.dataset.dayWeather = this.dayWeather;
  }

  syncTheme(shouldForce = false) {
    const nextTheme = this.root.classList.contains("dark-theme")
      ? "dark"
      : "light";

    if (!shouldForce && nextTheme === this.theme) return;

    const isEnteringDayMode = nextTheme === "light" && this.theme !== "light";
    this.theme = nextTheme;

    if (!this.dayWeather || isEnteringDayMode || shouldForce) {
      this.chooseDayWeather();
    }

    this.rebuildParticles();
    this.renderStaticFrame();
    this.startAnimation();
  }

  handleResize() {
    if (this.resizeFrameId) return;

    this.resizeFrameId = requestAnimationFrame(() => {
      this.resizeFrameId = null;
      this.resizeCanvas();
      this.rebuildParticles();
      this.renderStaticFrame();
    });
  }

  resizeCanvas() {
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    const pixelRatioLimit = this.width <= 768 ? 1.5 : 2;
    this.pixelRatio = Math.min(window.devicePixelRatio || 1, pixelRatioLimit);

    this.canvas.width = Math.floor(this.width * this.pixelRatio);
    this.canvas.height = Math.floor(this.height * this.pixelRatio);
    this.context.setTransform(
      this.pixelRatio,
      0,
      0,
      this.pixelRatio,
      0,
      0
    );
  }

  rebuildParticles() {
    const viewportArea = this.width * this.height;
    const starCount = clamp(Math.floor(viewportArea / 8500), 70, 180);
    const rainCount = clamp(Math.floor(viewportArea / 4200), 140, 320);
    const moteCount = clamp(Math.floor(viewportArea / 32000), 18, 48);
    const cloudCount = this.width <= 768 ? 4 : 7;

    this.stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * this.width,
      y: Math.random() * this.height,
      radius: randomBetween(0.55, 1.8),
      opacity: randomBetween(0.35, 0.9),
      phase: randomBetween(0, Math.PI * 2),
      speed: randomBetween(0.0008, 0.0026),
    }));

    this.rainDrops = Array.from({ length: rainCount }, () => ({
      x: Math.random() * this.width,
      y: Math.random() * this.height,
      length: randomBetween(16, 34),
      speed: randomBetween(520, 920),
      wind: randomBetween(45, 90),
      opacity: randomBetween(0.36, 0.72),
      width: randomBetween(0.75, 1.35),
    }));

    this.sunMotes = Array.from({ length: moteCount }, () => ({
      x: Math.random() * this.width,
      y: Math.random() * this.height,
      radius: randomBetween(0.8, 2.4),
      speedX: randomBetween(-3, 7),
      speedY: randomBetween(-10, -3),
      opacity: randomBetween(0.16, 0.45),
      phase: randomBetween(0, Math.PI * 2),
    }));

    this.clouds = Array.from({ length: cloudCount }, () => ({
      x: randomBetween(-120, this.width),
      y: randomBetween(this.height * 0.08, this.height * 0.62),
      scale: randomBetween(0.55, 1.35),
      speed: randomBetween(2.5, 8),
      opacity: randomBetween(0.08, 0.2),
    }));

    this.shootingStars = [];
    this.scheduleNextShootingStar(performance.now());
  }

  scheduleNextShootingStar(currentTime) {
    this.nextShootingStarTime = currentTime + randomBetween(3200, 7600);
  }

  spawnShootingStar(currentTime) {
    const speed = randomBetween(520, 760);

    this.shootingStars.push({
      x: randomBetween(-this.width * 0.05, this.width * 0.58),
      y: randomBetween(this.height * 0.04, this.height * 0.32),
      velocityX: speed,
      velocityY: speed * randomBetween(0.32, 0.48),
      age: 0,
      duration: randomBetween(0.75, 1.15),
    });

    this.scheduleNextShootingStar(currentTime);
  }

  handleVisibilityChange() {
    if (document.hidden) {
      this.stopAnimation();
      return;
    }

    this.previousFrameTime = performance.now();
    this.startAnimation();
  }

  handleReducedMotionChange() {
    if (this.reducedMotionQuery.matches) {
      this.stopAnimation();
      this.renderStaticFrame();
      return;
    }

    this.previousFrameTime = performance.now();
    this.startAnimation();
  }

  startAnimation() {
    if (
      this.animationFrameId ||
      document.hidden ||
      this.reducedMotionQuery.matches
    ) {
      return;
    }

    this.previousFrameTime = performance.now();
    this.animationFrameId = requestAnimationFrame(this.renderFrame);
  }

  stopAnimation() {
    if (!this.animationFrameId) return;

    cancelAnimationFrame(this.animationFrameId);
    this.animationFrameId = null;
  }

  renderStaticFrame() {
    if (!this.context) return;
    this.drawScene(performance.now(), 0);
  }

  renderFrame(currentTime) {
    this.animationFrameId = null;
    const deltaTime = Math.min(
      (currentTime - this.previousFrameTime) / 1000,
      MAX_FRAME_DELTA
    );

    this.previousFrameTime = currentTime;
    this.drawScene(currentTime, deltaTime);
    this.startAnimation();
  }

  drawScene(currentTime, deltaTime) {
    this.context.clearRect(0, 0, this.width, this.height);

    if (this.theme === "dark") {
      this.drawNightSky(currentTime, deltaTime);
    } else if (this.dayWeather === "rainy") {
      this.drawClouds(deltaTime, true);
      this.drawRain(deltaTime);
    } else {
      this.drawClouds(deltaTime, false);
      this.drawSunMotes(currentTime, deltaTime);
    }
  }

  drawClouds(deltaTime, isRainy) {
    const { context } = this;

    this.clouds.forEach((cloud) => {
      cloud.x += cloud.speed * deltaTime;
      const cloudWidth = 170 * cloud.scale;

      if (cloud.x - cloudWidth > this.width) {
        cloud.x = -cloudWidth;
        cloud.y = randomBetween(this.height * 0.08, this.height * 0.62);
      }

      context.save();
      context.translate(cloud.x, cloud.y);
      context.scale(cloud.scale, cloud.scale);
      context.fillStyle = isRainy
        ? `rgba(75, 103, 132, ${cloud.opacity + 0.06})`
        : `rgba(255, 255, 255, ${cloud.opacity})`;
      context.beginPath();
      context.ellipse(-45, 8, 56, 22, 0, 0, Math.PI * 2);
      context.ellipse(0, 0, 68, 30, 0, 0, Math.PI * 2);
      context.ellipse(48, 10, 48, 20, 0, 0, Math.PI * 2);
      context.fill();
      context.restore();
    });
  }

  drawSunMotes(currentTime, deltaTime) {
    const { context } = this;

    this.sunMotes.forEach((mote) => {
      mote.x += mote.speedX * deltaTime;
      mote.y += mote.speedY * deltaTime;

      if (mote.y < -10) {
        mote.y = this.height + 10;
        mote.x = Math.random() * this.width;
      }

      if (mote.x > this.width + 10) mote.x = -10;
      if (mote.x < -10) mote.x = this.width + 10;

      const shimmer =
        0.65 + Math.sin(currentTime * 0.0015 + mote.phase) * 0.35;
      context.globalAlpha = mote.opacity * shimmer;
      context.fillStyle = "#fff7c2";
      context.beginPath();
      context.arc(mote.x, mote.y, mote.radius, 0, Math.PI * 2);
      context.fill();
    });

    context.globalAlpha = 1;
  }

  drawRain(deltaTime) {
    const { context } = this;

    context.lineCap = "round";

    this.rainDrops.forEach((drop) => {
      drop.x += drop.wind * deltaTime;
      drop.y += drop.speed * deltaTime;

      if (drop.y - drop.length > this.height || drop.x > this.width + 30) {
        drop.x = randomBetween(-80, this.width);
        drop.y = randomBetween(-this.height * 0.35, -20);
      }

      const rainEndX =
        drop.x - (drop.wind / drop.speed) * drop.length;
      const rainEndY = drop.y - drop.length;

      context.lineWidth = drop.width + 0.9;
      context.strokeStyle = `rgba(44, 92, 132, ${drop.opacity * 0.58})`;
      context.beginPath();
      context.moveTo(drop.x, drop.y);
      context.lineTo(rainEndX, rainEndY);
      context.stroke();

      context.lineWidth = drop.width;
      context.strokeStyle = `rgba(224, 242, 254, ${drop.opacity})`;
      context.beginPath();
      context.moveTo(drop.x, drop.y);
      context.lineTo(rainEndX, rainEndY);
      context.stroke();
    });
  }

  drawNightSky(currentTime, deltaTime) {
    const { context } = this;
    const isReducedMotion = this.reducedMotionQuery.matches;

    this.stars.forEach((star) => {
      const twinkle = isReducedMotion
        ? star.opacity
        : star.opacity *
          (0.68 + Math.sin(currentTime * star.speed + star.phase) * 0.32);

      context.globalAlpha = clamp(twinkle, 0.12, 1);
      context.fillStyle = star.radius > 1.35 ? "#dcebfa" : "#ffffff";
      context.beginPath();
      context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      context.fill();
    });

    context.globalAlpha = 1;

    if (
      !isReducedMotion &&
      currentTime >= this.nextShootingStarTime &&
      this.shootingStars.length < 2
    ) {
      this.spawnShootingStar(currentTime);
    }

    this.shootingStars = this.shootingStars.filter((shootingStar) => {
      shootingStar.age += deltaTime;
      shootingStar.x += shootingStar.velocityX * deltaTime;
      shootingStar.y += shootingStar.velocityY * deltaTime;

      const progress = shootingStar.age / shootingStar.duration;
      if (progress >= 1) return false;

      const trailLength = 125;
      const directionLength = Math.hypot(
        shootingStar.velocityX,
        shootingStar.velocityY
      );
      const directionX = shootingStar.velocityX / directionLength;
      const directionY = shootingStar.velocityY / directionLength;
      const tailX = shootingStar.x - directionX * trailLength;
      const tailY = shootingStar.y - directionY * trailLength;
      const gradient = context.createLinearGradient(
        tailX,
        tailY,
        shootingStar.x,
        shootingStar.y
      );

      gradient.addColorStop(0, "rgba(255, 255, 255, 0)");
      gradient.addColorStop(
        1,
        `rgba(255, 255, 255, ${Math.sin(progress * Math.PI) * 0.9})`
      );

      context.strokeStyle = gradient;
      context.lineWidth = 1.8;
      context.lineCap = "round";
      context.beginPath();
      context.moveTo(tailX, tailY);
      context.lineTo(shootingStar.x, shootingStar.y);
      context.stroke();

      return true;
    });
  }
}

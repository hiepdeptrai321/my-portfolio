import { stories } from "../data/stories.js";

export class StoryModal {
  constructor({
    modalElement,
    onOpen,
    onClose,
    initialStoryKey = "storyEnglish",
    initialLanguage = "en",
  }) {
    if (!modalElement) {
      throw new Error("Story modal element was not found.");
    }

    this.modalElement = modalElement;
    this.onOpen = onOpen;
    this.onClose = onClose;
    this.storyKey = initialStoryKey;
    this.language = initialLanguage;

    this.bindEvents();
    this.render();
  }

  bindEvents() {
    const closeButton = this.modalElement.querySelector(".story-modal-close");

    closeButton.addEventListener("click", (event) => {
      event.preventDefault();
      this.close();
    });

    this.modalElement.addEventListener("click", (event) => {
      if (event.target === this.modalElement) {
        this.close();
      }
    });
  }

  render() {
    const story = stories[this.storyKey]?.[this.language];
    if (!story) return;

    const bodyElement = this.modalElement.querySelector(".story-modal-body");
    const paragraphElements = story.body.map((paragraphText) => {
      const paragraphElement = document.createElement("p");
      paragraphElement.className = "story-modal-body-text";
      paragraphElement.textContent = paragraphText;
      return paragraphElement;
    });

    bodyElement.replaceChildren(...paragraphElements);
    this.modalElement.querySelector(".story-modal-eyebrow").textContent =
      story.eyebrow;
    this.modalElement.querySelector(".story-modal-title").textContent =
      story.title;
    this.modalElement.querySelector(".story-modal-milestone").textContent =
      story.milestone;
    this.modalElement.querySelector(".story-modal-closing").textContent =
      story.closing;
  }

  open(storyKey) {
    if (stories[storyKey]) {
      this.storyKey = storyKey;
    }

    this.render();
    this.onOpen(this.modalElement);
  }

  setLanguage(language) {
    this.language = language;
    this.render();
  }

  close() {
    this.onClose(this.modalElement);
  }
}

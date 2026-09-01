export const SUPPORTED_LANGUAGES = ["en", "vi"];

export const translations = {
  en: {
    meta: {
      title: "Jason — Personal Story Portfolio",
      description:
        "Jason's personal story portfolio — a quiet room about his journey, values, life beyond coding, and what he is still exploring.",
      openGraphDescription:
        "Hi, I'm Jason. Explore my room and discover a personal journey I am still taking step by step.",
    },
    loading: {
      loading: "Loading...",
      enter: "Enter room",
      welcome: "~ Opening ~",
    },
    welcome: {
      greeting: "Hello, I’m Hiệp.",
    },
    controls: {
      group: "Website controls",
      mute: "Mute sound",
      unmute: "Unmute sound",
      volume: "Volume",
      volumeValue: (value) => `Volume ${value}%`,
      theme: "Toggle day and night mode",
      language: "Chuyển sang tiếng Việt",
      languageCode: "VI",
    },
    modal: {
      milestone: "Milestone",
      closeStory: "Close story modal",
      closeJourney: "Close journey modal",
      closeAbout: "Close about modal",
      closeContact: "Close contact modal",
    },
    journey: {
      label: "~ My Journey ~",
      introTitle: "Before I Found My Direction",
      introBody:
        "Before university, I was fairly introverted and sometimes found it difficult to make new friends. I knew almost nothing about coding; I only felt that I wanted to work with computers.",
      switchTitle: "Starting Again",
      switchBody:
        "I first studied Construction Engineering. After a period of feeling lost, I decided to begin again in Software Engineering. My family's support made that new beginning feel less uncertain.",
      exploreTitle: "Still Exploring",
      exploreBody:
        "I chose Software Engineering because I wanted to become a game developer. I am still exploring software, computer networks and IoT, one step at a time, to find the direction that fits me.",
    },
    about: {
      label: "~ About Me ~",
      greeting: "Hi, I'm Jason.",
      intro:
        "I'm fairly introverted, and meeting new people is not always easy for me. I try to be responsible in my work, care about the people around me, stay open-minded, and remain curious about new things.",
      growth:
        "I am still working on my discipline and tendency to be lazy. I do not have every step planned far ahead; I believe in moving forward little by little.",
      valuesTitle: "What matters to me",
      valueFamily: "Family, sincerity, and caring for the people around me.",
      valueCuriosity:
        "Staying curious and open to software, computer networks, and IoT.",
      valueGrowth:
        "Growing step by step instead of pretending to have everything figured out.",
    },
    contact: {
      label: "~ Say hello! ~",
      intro: "If something here resonates with you, feel free to say hello.",
      emailLabel: "Email Jason",
      githubLabel: "Jason on GitHub",
      linkedinLabel: "Jason on LinkedIn",
      facebookLabel: "Jason on Facebook",
    },
    hero: {
      canvasFallback:
        "The interactive room needs WebGL. You can still read the full story below.",
      title: "Hi, I'm Jason.",
      skip: "Skip the room",
      backToRoom: "Back to my room",
      noScript:
        "JavaScript is unavailable, but the full story is still available below.",
    },
    sections: {
      aboutEyebrow: "About Me",
      aboutTitle: "A quiet introduction",
      aboutBodyOne:
        "I'm fairly introverted, and meeting new people is not always easy for me. I try to be responsible in my work, care about the people around me, stay open-minded, and remain curious about new things.",
      aboutBodyTwo:
        "I am still working on my discipline and tendency to be lazy. I do not have everything planned far ahead. I believe in moving forward step by step.",
      journeyEyebrow: "My Journey",
      journeyTitle: "Starting again and still exploring",
      journeyBodyOne:
        "Before university, I knew almost nothing about coding. I only had the feeling that I wanted to work with computers, while school itself did not give me much excitement at the time.",
      journeyBodyTwo:
        "I first studied Construction Engineering. After a period of feeling lost, I decided to begin again in Software Engineering. My family's support helped me feel more at ease with that decision.",
      journeyBodyThree:
        "I originally chose Software Engineering because I wanted to become a game developer. Today, I am still exploring software, computer networks, and IoT to find the direction that fits me.",
      valuesEyebrow: "What I Value",
      valuesTitle: "The people and values that keep me grounded",
      valuesBodyOne:
        "Family support made it easier for me to start again. I value sincerity, caring for the people around me, and staying open to perspectives that are different from my own.",
      valuesBodyTwo:
        "TOEIC 925 was a small milestone. The score itself was not the most important part; the encouragement from my teachers and friends gave me more confidence, courage, and motivation to continue.",
      lifeEyebrow: "Life Beyond Coding",
      lifeTitle: "More than time in front of a screen",
      lifeBody:
        "Swimming is one of the ways I step away from the screen. This part of the portfolio is a reminder that learning and coding are only parts of a larger life.",
      futureEyebrow: "Looking Ahead",
      futureTitle: "One step at a time",
      futureBody:
        "I do not think too far into the future. I want to improve little by little, gain more experiences, become more independent, meet people on the same wavelength—including friends from other countries—and be able to help the people I love.",
      contactEyebrow: "GitHub & Contact",
      contactTitle: "Let's stay connected",
      contactBody:
        "If something here resonates with you, you can find me through these links.",
      profileLinksLabel: "Jason's profile links",
      email: "Email",
      footer:
        "Adapted from Andrew Woan's Soo-ah's Room Folio. Original credits and license are preserved in the repository.",
    },
  },
  vi: {
    meta: {
      title: "Hiệp — Portfolio câu chuyện cá nhân",
      description:
        "Portfolio câu chuyện cá nhân của Hiệp — một căn phòng yên tĩnh kể về hành trình, giá trị sống, cuộc sống ngoài coding và những điều tôi vẫn đang khám phá.",
      openGraphDescription:
        "Xin chào, mình là Hiệp. Hãy khám phá căn phòng và tìm hiểu hành trình mình vẫn đang đi từng bước một.",
    },
    loading: {
      loading: "Đang tải...",
      enter: "Vào phòng",
      welcome: "~ Đang mở ~",
    },
    welcome: {
      greeting: "Hello, I’m Hiệp.",
    },
    controls: {
      group: "Điều khiển website",
      mute: "Tắt âm thanh",
      unmute: "Bật âm thanh",
      volume: "Âm lượng",
      volumeValue: (value) => `Âm lượng ${value}%`,
      theme: "Chuyển chế độ ngày và đêm",
      language: "Switch to English",
      languageCode: "EN",
    },
    modal: {
      milestone: "Cột mốc",
      closeStory: "Đóng câu chuyện",
      closeJourney: "Đóng hành trình",
      closeAbout: "Đóng phần giới thiệu",
      closeContact: "Đóng phần liên hệ",
    },
    journey: {
      label: "~ Hành trình của mình ~",
      introTitle: "Trước khi tìm thấy hướng đi",
      introBody:
        "Trước đại học, mình khá hướng nội và đôi khi gặp khó khăn khi làm quen bạn mới. Mình gần như chưa biết gì về coding; mình chỉ có cảm giác rằng bản thân muốn làm việc với máy tính.",
      switchTitle: "Bắt đầu lại",
      switchBody:
        "Ban đầu mình học Kỹ thuật xây dựng. Sau một khoảng thời gian mất định hướng, mình quyết định bắt đầu lại với Kỹ thuật phần mềm. Sự ủng hộ của gia đình khiến khởi đầu mới này bớt bất an hơn.",
      exploreTitle: "Vẫn đang khám phá",
      exploreBody:
        "Mình chọn Kỹ thuật phần mềm vì từng muốn trở thành game developer. Hiện tại, mình vẫn đang khám phá phần mềm, mạng máy tính và IoT, từng bước một, để tìm ra hướng phù hợp với bản thân.",
    },
    about: {
      label: "~ Về mình ~",
      greeting: "Xin chào, mình là Hiệp.",
      intro:
        "Mình khá hướng nội và việc làm quen với người mới không phải lúc nào cũng dễ dàng. Mình cố gắng có trách nhiệm trong công việc, quan tâm đến mọi người xung quanh, giữ tư duy cởi mở và luôn tò mò về những điều mới.",
      growth:
        "Mình vẫn đang cải thiện tính kỷ luật và sự lười biếng của bản thân. Mình không lên kế hoạch quá xa cho mọi bước đi; mình tin vào việc tiến lên từng chút một.",
      valuesTitle: "Những điều quan trọng với mình",
      valueFamily: "Gia đình, sự chân thành và quan tâm đến mọi người xung quanh.",
      valueCuriosity:
        "Giữ sự tò mò và cởi mở với phần mềm, mạng máy tính và IoT.",
      valueGrowth:
        "Tiến bộ từng bước thay vì giả vờ rằng mình đã hiểu rõ mọi thứ.",
    },
    contact: {
      label: "~ Hãy kết nối nhé! ~",
      intro: "Nếu bạn tìm thấy sự đồng cảm ở đây, hãy gửi cho mình một lời chào.",
      emailLabel: "Gửi email cho Hiệp",
      githubLabel: "GitHub của Hiệp",
      linkedinLabel: "LinkedIn của Hiệp",
      facebookLabel: "Facebook của Hiệp",
    },
    hero: {
      canvasFallback:
        "Căn phòng tương tác cần WebGL. Bạn vẫn có thể đọc toàn bộ câu chuyện ở bên dưới.",
      title: "Xin chào, mình là Hiệp.",
      skip: "Bỏ qua căn phòng",
      backToRoom: "Trở lại căn phòng",
      noScript:
        "JavaScript hiện không khả dụng, nhưng toàn bộ câu chuyện vẫn nằm ở bên dưới.",
    },
    sections: {
      aboutEyebrow: "Về mình",
      aboutTitle: "Một lời giới thiệu nhẹ nhàng",
      aboutBodyOne:
        "Mình khá hướng nội và việc làm quen với người mới không phải lúc nào cũng dễ dàng. Mình cố gắng có trách nhiệm trong công việc, quan tâm đến mọi người xung quanh, giữ tư duy cởi mở và luôn tò mò về những điều mới.",
      aboutBodyTwo:
        "Mình vẫn đang cải thiện tính kỷ luật và sự lười biếng của bản thân. Mình không lên kế hoạch quá xa cho mọi thứ. Mình tin vào việc tiến lên từng bước một.",
      journeyEyebrow: "Hành trình của mình",
      journeyTitle: "Bắt đầu lại và tiếp tục khám phá",
      journeyBodyOne:
        "Trước đại học, mình gần như chưa biết gì về coding. Mình chỉ có cảm giác rằng bản thân muốn làm việc với máy tính, trong khi việc học ở trường lúc đó không tạo cho mình nhiều hứng thú.",
      journeyBodyTwo:
        "Ban đầu mình học Kỹ thuật xây dựng. Sau một khoảng thời gian mất định hướng, mình quyết định bắt đầu lại với Kỹ thuật phần mềm. Sự ủng hộ của gia đình giúp mình cảm thấy yên tâm hơn với quyết định đó.",
      journeyBodyThree:
        "Ban đầu mình chọn Kỹ thuật phần mềm vì muốn trở thành game developer. Hiện tại, mình vẫn đang khám phá phần mềm, mạng máy tính và IoT để tìm ra hướng phù hợp nhất với bản thân.",
      valuesEyebrow: "Điều mình trân trọng",
      valuesTitle: "Những con người và giá trị giúp mình vững vàng",
      valuesBodyOne:
        "Sự ủng hộ của gia đình giúp mình an tâm bắt đầu lại. Mình trân trọng sự chân thành, việc quan tâm đến mọi người xung quanh và luôn cởi mở với những góc nhìn khác mình.",
      valuesBodyTwo:
        "TOEIC 925 là một cột mốc nhỏ. Bản thân điểm số không phải phần quan trọng nhất; lời động viên từ thầy cô và bạn bè đã cho mình thêm sự tự tin, dũng cảm và động lực để tiếp tục.",
      lifeEyebrow: "Cuộc sống ngoài coding",
      lifeTitle: "Không chỉ là thời gian trước màn hình",
      lifeBody:
        "Bơi lội là một trong những cách giúp mình rời khỏi màn hình. Phần này nhắc mình rằng học tập và coding chỉ là một phần của cuộc sống rộng lớn hơn.",
      futureEyebrow: "Nhìn về phía trước",
      futureTitle: "Từng bước một",
      futureBody:
        "Mình không nghĩ quá xa về tương lai. Mình muốn tiến bộ từng chút, có thêm nhiều trải nghiệm, trở nên tự lập hơn, gặp những người có cùng tần số—bao gồm bạn bè từ các quốc gia khác—và có khả năng giúp đỡ những người mình yêu quý.",
      contactEyebrow: "GitHub và liên hệ",
      contactTitle: "Hãy giữ kết nối",
      contactBody:
        "Nếu bạn tìm thấy sự đồng cảm ở đây, bạn có thể liên hệ với mình qua những đường dẫn này.",
      profileLinksLabel: "Các liên kết của Hiệp",
      email: "Email",
      footer:
        "Được phát triển từ Soo-ah's Room Folio của Andrew Woan. Credit gốc và giấy phép vẫn được giữ nguyên trong repository.",
    },
  },
};

export function getInitialLanguage() {
  const urlLanguage = new URLSearchParams(window.location.search).get("lang");
  if (SUPPORTED_LANGUAGES.includes(urlLanguage)) return urlLanguage;

  return "en";
}

export function getTranslation(language, key) {
  return key.split(".").reduce((value, segment) => value?.[segment], translations[language]);
}

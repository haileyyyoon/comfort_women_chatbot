(() => {
  const chatLog = document.getElementById('chat-log');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const suggestions = document.getElementById('suggestions');
  const resetBtn = document.getElementById('reset-btn');
  const langSelect = document.getElementById('lang-select');

  // ----- Interface translations -------------------------------------------
  // Keys mirror the data-i18n attributes in chatbot.html. "auto" reuses the
  // English chrome but still tells the server to reply in the user's language.
  // The chatbot's name is 나누미 in Korean and "Nanumi" in every other language.
  const I18N = {
    en: {
      lang: 'en',
      title: 'House of Sharing Chatbot Nanumi',
      intro:
        'Nanumi is an AI chatbot that answers questions using testimony, historical records, ' +
        'and research gathered by the House of Sharing (나눔의 집) and related sources documenting ' +
        'Japan’s wartime military sexual slavery system. Answers are drawn strictly from these ' +
        'records — if something isn’t in them, Nanumi will say so.',
      welcome:
        'Welcome! I’m Nanumi, the House of Sharing’s chatbot. You can ask about survivors’ ' +
        'testimonies, the history of the comfort station system, the Wednesday Demonstrations, ' +
        'government responses, or the House of Sharing itself. What would you like to know?',
      reset: 'New conversation',
      placeholder: 'Please feel free to ask me anything about this history…',
      botLabel: 'Nanumi',
      youLabel: 'You',
      languageLabel: 'Answer language',
      suggestionsLabel: 'Sample questions',
      suggestions: [
        'Who were the Japanese military ‘comfort women’ victims?',
        'Tell me about the House of Sharing',
        'Who was Kim Hak-soon?',
        'What was the Kono Statement?',
      ],
      footerDisclaimer:
        'Answers are AI-generated from the museum’s records and may contain errors. ' +
        'Please contact the House of Sharing to confirm important details.',
      noAnswer: 'Sorry, no answer was found.',
      errorGeneric: 'Something went wrong. Please try again.',
      errorNetwork: 'Could not reach the server. Please check your connection and try again.',
    },
    ko: {
      lang: 'ko',
      title: '나눔의 집 챗봇 나누미',
      intro:
        '나누미는 나눔의 집과 관련 자료에 담긴 증언, 역사 기록, 연구 자료를 바탕으로 일본군 ' +
        '‘위안부’ 피해의 역사에 관한 질문에 답해 드리는 AI 챗봇입니다. 답변은 오직 이 기록에만 ' +
        '근거하며, 기록에 없는 내용은 솔직하게 말씀드립니다.',
      welcome:
        '안녕하세요, 나눔의 집 챗봇 나누미입니다. 피해자 할머니들의 증언과 일본군 ‘위안부’ ' +
        '제도의 역사, 수요시위, 정부의 대응, 나눔의 집에 대해 질문하실 수 있습니다. ' +
        '무엇이 궁금하신가요?',
      reset: '새 대화',
      placeholder: '궁금한 점이 있으시면 편하게 질문해 주세요…',
      botLabel: '나누미',
      youLabel: '나',
      languageLabel: '답변 언어',
      suggestionsLabel: '예시 질문',
      suggestions: [
        '일본군 위안부 피해자란?',
        '나눔의 집에 대해서 알려줘',
        '김학순 할머니는 어떤 분이었어?',
        '고노 담화는 무엇이었나요?',
      ],
      footerDisclaimer:
        '답변은 박물관 자료를 바탕으로 AI가 생성하며, 오류가 있을 수 있습니다. ' +
        '중요한 내용은 나눔의 집에 문의하여 확인해 주시기 바랍니다.',
      noAnswer: '죄송합니다. 답변을 찾지 못했습니다.',
      errorGeneric: '문제가 발생했습니다. 다시 시도해 주세요.',
      errorNetwork: '서버에 연결할 수 없습니다. 연결 상태를 확인한 후 다시 시도해 주세요.',
    },
    ja: {
      lang: 'ja',
      title: 'ナヌムの家チャットボット Nanumi',
      intro:
        'Nanumiは、ナヌムの家（House of Sharing）や関連資料に収められた証言・歴史記録・研究に基づいて、' +
        '日本軍「慰安婦」被害の歴史に関する質問にお答えするAIチャットボットです。回答はこれらの記録のみに' +
        '基づいており、記録にない場合はその旨を正直にお伝えします。',
      welcome:
        'こんにちは。ナヌムの家のチャットボット、Nanumiです。被害者の方々の証言、慰安所制度の歴史、' +
        '水曜デモ、政府の対応、ナヌムの家についてご質問いただけます。何をお知りになりたいですか？',
      reset: '新しい会話',
      placeholder: '気になることがあれば、お気軽にご質問ください…',
      botLabel: 'Nanumi',
      youLabel: 'あなた',
      languageLabel: '回答の言語',
      suggestionsLabel: '質問の例',
      suggestions: [
        '日本軍「慰安婦」被害者とは？',
        'ナヌムの家について教えてください',
        '金学順（キム・ハクスン）さんはどのような方でしたか？',
        '河野談話とは何でしたか？',
      ],
      footerDisclaimer:
        '回答は博物館の資料をもとにAIが生成しており、誤りが含まれる場合があります。' +
        '重要な内容はナヌムの家にお問い合わせのうえご確認ください。',
      noAnswer: '申し訳ありません。回答が見つかりませんでした。',
      errorGeneric: '問題が発生しました。もう一度お試しください。',
      errorNetwork: 'サーバーに接続できませんでした。接続を確認して再度お試しください。',
    },
    zh: {
      lang: 'zh',
      title: '分享之家聊天机器人 Nanumi',
      intro:
        'Nanumi 是一个AI聊天机器人，依据分享之家（나눔의 집）及相关来源收集的证词、历史记录与研究，' +
        '回答有关日军“慰安妇”受害历史的问题。回答仅依据这些记录；如果记录中没有相关信息，Nanumi 会如实说明。',
      welcome:
        '您好，我是分享之家的聊天机器人 Nanumi。您可以询问幸存者的证词、慰安所制度的历史、' +
        '周三示威、政府的回应，或分享之家本身。您想了解什么？',
      reset: '新对话',
      placeholder: '如果您有任何问题，欢迎随时提问…',
      botLabel: 'Nanumi',
      youLabel: '您',
      languageLabel: '回答语言',
      suggestionsLabel: '示例问题',
      suggestions: [
        '什么是日军“慰安妇”受害者？',
        '请介绍一下分享之家',
        '金学顺是谁？',
        '河野谈话是什么？',
      ],
      footerDisclaimer:
        '回答由AI根据博物馆资料生成，可能存在错误。重要信息请与分享之家联系确认。',
      noAnswer: '抱歉，未找到答案。',
      errorGeneric: '出现问题，请重试。',
      errorNetwork: '无法连接服务器，请检查网络后重试。',
    },
    es: {
      lang: 'es',
      title: 'Nanumi: Chatbot de la Casa del Compartir',
      intro:
        'Nanumi es un chatbot de IA que responde a las preguntas a partir de testimonios, ' +
        'registros históricos e investigaciones reunidos por la Casa del Compartir (나눔의 집) y fuentes relacionadas ' +
        'que documentan el sistema de esclavitud sexual militar de Japón durante la guerra. ' +
        'Las respuestas se basan únicamente en estos registros; si algo no consta en ellos, ' +
        'Nanumi se lo indicará.',
      welcome:
        'Bienvenido/a. Soy Nanumi, el chatbot de la Casa del Compartir. Puede preguntar sobre ' +
        'los testimonios de las sobrevivientes, la historia del sistema de «estaciones de ' +
        'consuelo», las Manifestaciones de los Miércoles, las respuestas de los gobiernos o la ' +
        'propia Casa del Compartir. ¿Qué le gustaría saber?',
      reset: 'Nueva conversación',
      placeholder: 'Si tiene alguna pregunta, no dude en preguntarme…',
      botLabel: 'Nanumi',
      youLabel: 'Usted',
      languageLabel: 'Idioma de la respuesta',
      suggestionsLabel: 'Preguntas de ejemplo',
      suggestions: [
        '¿Quiénes fueron las víctimas del sistema de «mujeres de consuelo»?',
        'Cuénteme sobre la Casa del Compartir',
        '¿Quién fue Kim Hak-soon?',
        '¿Qué fue la Declaración de Kono?',
      ],
      footerDisclaimer:
        'Las respuestas son generadas por IA a partir de los registros del museo y pueden ' +
        'contener errores. Para confirmar detalles importantes, contacte con la Casa del Compartir.',
      noAnswer: 'Lo sentimos, no se encontró ninguna respuesta.',
      errorGeneric: 'Algo salió mal. Inténtelo de nuevo.',
      errorNetwork: 'No se pudo conectar con el servidor. Compruebe su conexión e inténtelo de nuevo.',
    },
    fr: {
      lang: 'fr',
      title: 'Nanumi : Chatbot de la Maison du Partage',
      intro:
        'Nanumi est un chatbot d’IA qui répond aux questions à partir de témoignages, de ' +
        'documents historiques et de recherches rassemblés par la Maison du Partage (나눔의 집) et des sources connexes ' +
        'documentant le système d’esclavage sexuel militaire du Japon pendant la guerre. ' +
        'Les réponses s’appuient uniquement sur ces documents ; si une information n’y figure ' +
        'pas, Nanumi vous le précisera.',
      welcome:
        'Bienvenue. Je suis Nanumi, le chatbot de la Maison du Partage. Vous pouvez poser des ' +
        'questions sur les témoignages des survivantes, l’histoire du système des « stations de ' +
        'réconfort », les Manifestations du mercredi, les réponses des gouvernements ou la ' +
        'Maison du Partage elle-même. Que souhaitez-vous savoir ?',
      reset: 'Nouvelle conversation',
      placeholder: 'Si vous avez une question, n’hésitez pas à me la poser…',
      botLabel: 'Nanumi',
      youLabel: 'Vous',
      languageLabel: 'Langue de la réponse',
      suggestionsLabel: 'Exemples de questions',
      suggestions: [
        'Qui étaient les victimes du système des « femmes de réconfort » ?',
        'Parlez-moi de la Maison du Partage',
        'Qui était Kim Hak-soon ?',
        'Qu’était la déclaration de Kono ?',
      ],
      footerDisclaimer:
        'Les réponses sont générées par une IA à partir des documents du musée et peuvent ' +
        'contenir des erreurs. Pour confirmer les informations importantes, veuillez contacter ' +
        'la Maison du Partage.',
      noAnswer: 'Désolé, aucune réponse n’a été trouvée.',
      errorGeneric: 'Une erreur s’est produite. Veuillez réessayer.',
      errorNetwork: 'Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.',
    },
    de: {
      lang: 'de',
      title: 'House-of-Sharing-Chatbot Nanumi',
      intro:
        'Nanumi ist ein KI-Chatbot und beantwortet Fragen auf der Grundlage von Zeugenaussagen, ' +
        'historischen Aufzeichnungen und Forschungen, die vom House of Sharing (나눔의 집) und verwandten ' +
        'Quellen zum System der militärischen Sexsklaverei Japans während des Krieges ' +
        'zusammengetragen wurden. Die Antworten stützen sich ausschließlich auf diese ' +
        'Aufzeichnungen; fehlt eine Information, sagt Nanumi das offen.',
      welcome:
        'Willkommen! Ich bin Nanumi, der Chatbot des House of Sharing. Sie können nach den ' +
        'Zeugenaussagen der Überlebenden, der Geschichte des Systems der „Troststationen“, den ' +
        'Mittwochsdemonstrationen, den Reaktionen der Regierungen oder dem House of Sharing ' +
        'selbst fragen. Was möchten Sie wissen?',
      reset: 'Neues Gespräch',
      placeholder: 'Wenn Sie eine Frage haben, stellen Sie sie mir gerne…',
      botLabel: 'Nanumi',
      youLabel: 'Sie',
      languageLabel: 'Antwortsprache',
      suggestionsLabel: 'Beispielfragen',
      suggestions: [
        'Wer waren die Opfer des „Trostfrauen“-Systems?',
        'Erzählen Sie mir vom House of Sharing',
        'Wer war Kim Hak-soon?',
        'Was war die Kono-Erklärung?',
      ],
      footerDisclaimer:
        'Die Antworten werden von einer KI auf Grundlage der Museumsunterlagen erstellt und ' +
        'können Fehler enthalten. Bitte wenden Sie sich zur Bestätigung wichtiger Angaben an ' +
        'das House of Sharing.',
      noAnswer: 'Leider wurde keine Antwort gefunden.',
      errorGeneric: 'Etwas ist schiefgelaufen. Bitte versuchen Sie es erneut.',
      errorNetwork: 'Der Server ist nicht erreichbar. Bitte prüfen Sie Ihre Verbindung und versuchen Sie es erneut.',
    },
  };

  // Maps a <select> value (also the language sent to the server) to a chrome
  // translation set. "auto" keeps the English interface.
  const CHROME_FOR_VALUE = {
    auto: 'en',
    English: 'en',
    Korean: 'ko',
    Japanese: 'ja',
    'Chinese (Simplified)': 'zh',
    Spanish: 'es',
    French: 'fr',
    German: 'de',
  };

  const STORAGE_KEY = 'cw-answer-language';
  let t = I18N.en; // current chrome translation set

  function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function applyLanguage(value) {
    t = I18N[CHROME_FOR_VALUE[value] || 'en'];
    document.documentElement.lang = t.lang;

    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (t[key]) el.textContent = t[key];
    });

    userInput.placeholder = t.placeholder;

    // The small line above the heading pairs the two names: it shows the
    // Korean name normally, and the English name when the page is in Korean.
    const brandKr = document.querySelector('.brand-kr');
    if (brandKr) {
      brandKr.textContent = t.lang === 'ko' ? 'House of Sharing Chatbot Nanumi' : '나눔의 집 챗봇 나누미';
    }

    if (suggestions) {
      suggestions.querySelectorAll('.chip').forEach((chip, i) => {
        if (t.suggestions[i]) chip.textContent = t.suggestions[i];
      });
    }
  }

  function appendMessage(role, text) {
    const wrap = document.createElement('div');
    wrap.className = `msg msg-${role}`;

    const label = document.createElement('span');
    label.className = 'msg-label';
    label.textContent = role === 'user' ? t.youLabel : t.botLabel;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.textContent = text;

    wrap.appendChild(label);
    wrap.appendChild(bubble);
    chatLog.appendChild(wrap);
    scrollToBottom();
    return bubble;
  }

  function appendLoading() {
    const wrap = document.createElement('div');
    wrap.className = 'msg msg-bot';

    const label = document.createElement('span');
    label.className = 'msg-label';
    label.textContent = t.botLabel;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble is-loading';
    bubble.innerHTML = '<span></span><span></span><span></span>';

    wrap.appendChild(label);
    wrap.appendChild(bubble);
    chatLog.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  async function sendQuestion(question) {
    if (!question) return;

    appendMessage('user', question);

    const loadingEl = appendLoading();

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, language: langSelect ? langSelect.value : 'auto' }),
      });

      const data = await res.json().catch(() => ({}));
      loadingEl.remove();

      if (!res.ok) {
        const bubble = appendMessage('bot', data.response || t.errorGeneric);
        bubble.classList.add('is-error');
        return;
      }

      appendMessage('bot', data.response || t.noAnswer);
    } catch (err) {
      loadingEl.remove();
      const bubble = appendMessage('bot', t.errorNetwork);
      bubble.classList.add('is-error');
    }
  }

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const question = userInput.value.trim();
    if (!question) return;
    userInput.value = '';
    sendQuestion(question);
  });

  if (suggestions) {
    suggestions.querySelectorAll('.chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        sendQuestion(chip.textContent.trim());
      });
    });
  }

  if (langSelect) {
    langSelect.addEventListener('change', () => {
      applyLanguage(langSelect.value);
      try {
        localStorage.setItem(STORAGE_KEY, langSelect.value);
      } catch (err) {
        // localStorage may be unavailable (private mode); selection still works for this session.
      }
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      try {
        await fetch('/reset', { method: 'POST' });
      } catch (err) {
        // Non-fatal: the server session will just carry over.
      }
      chatLog.innerHTML = '';
      appendMessage('bot', t.welcome);
    });
  }

  // ----- Init --------------------------------------------------------------
  let saved = 'auto';
  try {
    saved = localStorage.getItem(STORAGE_KEY) || 'auto';
  } catch (err) {
    // ignore
  }
  if (langSelect && CHROME_FOR_VALUE[saved]) {
    langSelect.value = saved;
  }
  applyLanguage(langSelect ? langSelect.value : 'auto');

  userInput.focus();
})();

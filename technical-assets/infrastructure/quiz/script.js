(function () {
  "use strict";

  let config = {};
  let questions = [];
  let section1Questions = [];
  let section2Questions = [];
  let timerInterval = null;
  let secondsRemaining = 0;

  // Returning-user state
  let previousSubmission = null;
  let isRetry = false;
  let currentTab = "quiz";

  // DOM elements
  const welcomeScreen = document.getElementById("welcome-screen");
  const tabContainer = document.getElementById("tab-container");
  const infoForm = document.getElementById("info-form");
  const startBtn = document.getElementById("start-btn");
  const nameInput = document.getElementById("name");
  const emailInput = document.getElementById("email");
  const emailError = document.getElementById("email-error");
  const returningBanner = document.getElementById("returning-user-banner");
  const returningInfo = document.getElementById("returning-user-info");

  // Tab elements
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanelQuiz = document.getElementById("tab-panel-quiz");
  const tabPanelResponses = document.getElementById("tab-panel-responses");

  // Quiz tab elements
  const quizLanding = document.getElementById("quiz-landing");
  const quizActive = document.getElementById("quiz-active");
  const quizResult = document.getElementById("quiz-result");
  const startQuizBtn = document.getElementById("start-quiz-btn");
  const submitQuizBtn = document.getElementById("submit-quiz-btn");
  const retryQuizBtn = document.getElementById("retry-quiz-btn");
  const continueToFrqBtn = document.getElementById("continue-to-frq-btn");
  const mcqQuestionsContainer = document.getElementById("mcq-questions-container");
  const mcqAnswerSummary = document.getElementById("mcq-answer-summary");
  const landingScoreBanner = document.getElementById("landing-score-banner");
  const resultScoreBanner = document.getElementById("result-score-banner");
  const quizScoreDisplay = document.getElementById("quiz-score-display");
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");
  const progressWrapper = document.getElementById("progress-wrapper");
  const timerDisplay = document.getElementById("timer-display");

  // Responses tab elements
  const saveResponsesBtn = document.getElementById("save-responses-btn");
  const frqQuestionsContainer = document.getElementById("frq-questions-container");
  const responsesSaveStatus = document.getElementById("responses-save-status");

  // --- Init ---
  async function init() {
    try {
      var [configRes, questionsRes] = await Promise.all([
        fetch("config.json"),
        fetch("questions.json"),
      ]);
      config = await configRes.json();
      questions = await questionsRes.json();
    } catch (err) {
      console.error("Failed to load config or questions:", err);
      document.getElementById("quiz-title").textContent = "Error loading quiz";
      document.getElementById("quiz-description").textContent =
        "Could not load quiz data. Please make sure config.json and questions.json are available.";
      startBtn.disabled = true;
      return;
    }

    // Determine org from ?org= query param, falling back to config.defaultOrg, then "csu"
    var params = new URLSearchParams(window.location.search);
    var orgKey = params.get("org") || config.defaultOrg || "csu";
    var orgConfig = (config.orgs && config.orgs[orgKey]) || (config.orgs && config.orgs["csu"]) || {};

    // Merge org-specific values into config
    config.title = orgConfig.title || config.title || "DxHub Summer Hackathon";
    config.description = orgConfig.description || config.description || "";

    // Set org logo
    if (orgConfig.logo) {
      document.getElementById("org-logo").src = "logos/" + orgConfig.logo;
    }

    // Set email label if provided
    if (orgConfig.emailLabel) {
      document.querySelector('label[for="email"]').textContent = orgConfig.emailLabel;
    }

    section1Questions = questions.filter(function (q) { return q.section === 1; });
    section2Questions = questions.filter(function (q) { return q.section === 2; });

    document.getElementById("header-title").textContent = config.title;
    document.getElementById("quiz-title").textContent = config.title;
    document.getElementById("quiz-description").textContent = config.description;
    document.title = config.title;

    if (!config.showProgressBar) {
      progressWrapper.style.display = "none";
    }
  }

  // --- Screen navigation ---
  function showScreen(screen) {
    [welcomeScreen, tabContainer].forEach(function (s) {
      s.classList.remove("active");
    });
    screen.classList.add("active");
    window.scrollTo(0, 0);
  }

  // --- Tab switching ---
  function switchTab(tabName) {
    currentTab = tabName;

    tabBtns.forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    tabPanelQuiz.classList.toggle("active", tabName === "quiz");
    tabPanelResponses.classList.toggle("active", tabName === "responses");

    window.scrollTo(0, 0);
  }

  // --- Quiz tab internal state management ---
  function showQuizLandingFresh() {
    quizLanding.style.display = "block";
    quizActive.style.display = "none";
    quizResult.style.display = "none";
    quizScoreDisplay.style.display = "none";
    startQuizBtn.textContent = "Start Quiz";
  }

  function showQuizLandingWithScore(score, total, attempts) {
    quizLanding.style.display = "block";
    quizActive.style.display = "none";
    quizResult.style.display = "none";

    var pct = total > 0 ? Math.round((score / total) * 100) : 0;
    landingScoreBanner.innerHTML =
      '<div class="score-label">Your Best Score</div>' +
      '<div class="score-value">' + score + " / " + total + "</div>" +
      '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="attempt-info">' + attempts + " attempt" + (attempts !== 1 ? "s" : "") + "</div>";
    quizScoreDisplay.style.display = "block";
    startQuizBtn.textContent = "Retry Quiz";
  }

  function showQuizActive() {
    quizLanding.style.display = "none";
    quizActive.style.display = "block";
    quizResult.style.display = "none";
  }

  function showQuizResult() {
    quizLanding.style.display = "none";
    quizActive.style.display = "none";
    quizResult.style.display = "block";
    window.scrollTo(0, 0);
    markTabCompleted("quiz");
  }

  // --- Lookup returning user ---
  async function lookupUser(email) {
    if (!config.apiBaseUrl) return;

    var trimmed = email.trim().toLowerCase();
    if (!trimmed) return;

    try {
      var res = await fetch(
        config.apiBaseUrl + "/submission/" + encodeURIComponent(trimmed)
      );
      var data = await res.json();

      if (data.found && data.submission) {
        previousSubmission = data.submission;
        isRetry = true;

        if (previousSubmission.name && !nameInput.value.trim()) {
          nameInput.value = previousSubmission.name;
        }

        var attempts = previousSubmission.mcqAttempts || 0;
        var score = previousSubmission.mcqScore || 0;
        var total = previousSubmission.mcqTotal || 0;
        var quizTaken = previousSubmission.quizTaken || false;

        if (quizTaken) {
          returningInfo.textContent =
            attempts + " previous attempt" + (attempts !== 1 ? "s" : "") +
            ". Best MCQ score: " + score + "/" + total + ".";
        } else {
          returningInfo.textContent = "You have saved responses. Your answers will be pre-filled.";
        }

        returningBanner.style.display = "block";
        startBtn.textContent = "Continue";
      } else {
        previousSubmission = null;
        isRetry = false;
        returningBanner.style.display = "none";
        startBtn.textContent = "Get Started";
      }
    } catch (err) {
      console.warn("Could not look up user:", err);
    }
  }

  // --- Render Section 1 (MCQ) questions ---
  function renderSection1Questions() {
    mcqQuestionsContainer.innerHTML = "";
    var list = config.shuffleQuestions ? shuffle(section1Questions.slice()) : section1Questions;

    list.forEach(function (q, idx) {
      var card = document.createElement("div");
      card.className = "question-card";
      card.dataset.questionId = q.id;

      var inner =
        '<div class="question-number">Question ' + (idx + 1) +
        " of " + list.length + "</div>" +
        '<span class="question-type-badge mcq">Multiple Choice</span>' +
        '<div class="question-text">' + escapeHtml(q.question) + "</div>";

      var shuffledOptions = shuffle(q.options.slice());
      inner += '<ul class="options-list">';
      shuffledOptions.forEach(function (opt, oi) {
        var inputId = "q" + q.id + "_opt" + oi;
        inner +=
          "<li>" +
          '<label for="' + inputId + '">' +
          '<input type="radio" id="' + inputId +
          '" name="q' + q.id +
          '" value="' + escapeAttr(opt) + '">' +
          "<span>" + escapeHtml(opt) + "</span>" +
          "</label></li>";
      });
      inner += "</ul>";

      card.innerHTML = inner;
      mcqQuestionsContainer.appendChild(card);
    });

    mcqQuestionsContainer.querySelectorAll('input[type="radio"]').forEach(function (r) {
      r.addEventListener("change", updateMcqProgress);
    });
  }

  // --- Render Section 2 (FRQ / matching selection) questions ---
  function renderSection2Questions() {
    frqQuestionsContainer.innerHTML = "";

    section2Questions.forEach(function (q, idx) {
      var card = document.createElement("div");
      card.className = "question-card";
      card.dataset.questionId = q.id;

      var typeBadge = q.type === "mcq"
        ? '<span class="question-type-badge mcq">Selection</span>'
        : '<span class="question-type-badge frq">Free Response</span>';

      var inner =
        '<div class="question-number">Question ' + (idx + 1) +
        " of " + section2Questions.length + "</div>" +
        typeBadge +
        '<div class="question-text">' + escapeHtml(q.question) + "</div>";

      if (q.type === "frq") {
        var maxLen = q.maxLength || 1000;
        inner +=
          '<textarea class="frq-textarea" data-qid="' + q.id +
          '" maxlength="' + maxLen +
          '" placeholder="Type your answer here..."></textarea>' +
          '<div class="char-count" id="cc-' + q.id + '">0 / ' + maxLen + "</div>";
      } else if (q.type === "mcq") {
        inner += '<ul class="options-list">';
        q.options.forEach(function (opt, oi) {
          var inputId = "s2q" + q.id + "_opt" + oi;
          inner +=
            "<li>" +
            '<label for="' + inputId + '">' +
            '<input type="radio" id="' + inputId +
            '" name="s2q' + q.id +
            '" value="' + escapeAttr(opt) + '">' +
            "<span>" + escapeHtml(opt) + "</span>" +
            "</label></li>";
        });
        inner += "</ul>";
      }

      card.innerHTML = inner;
      frqQuestionsContainer.appendChild(card);
    });

    // Attach char count listeners
    frqQuestionsContainer.querySelectorAll(".frq-textarea").forEach(function (ta) {
      var qid = ta.dataset.qid;
      var q = section2Questions.find(function (x) { return String(x.id) === qid; });
      var maxLen = (q && q.maxLength) || 1000;
      ta.addEventListener("input", function () {
        var cc = document.getElementById("cc-" + qid);
        cc.textContent = ta.value.length + " / " + maxLen;
        cc.classList.toggle("over", ta.value.length >= maxLen);
      });
    });
  }

  // --- Pre-fill section 2 for returning users ---
  function prefillSection2(savedAnswers) {
    savedAnswers.forEach(function (prev) {
      if (prev.type === "frq" && prev.answer) {
        var ta = frqQuestionsContainer.querySelector('.frq-textarea[data-qid="' + prev.id + '"]');
        if (ta) {
          ta.value = prev.answer;
          var q = section2Questions.find(function (x) { return x.id === prev.id; });
          var maxLen = (q && q.maxLength) || 1000;
          var cc = document.getElementById("cc-" + prev.id);
          if (cc) {
            cc.textContent = prev.answer.length + " / " + maxLen;
            cc.classList.toggle("over", prev.answer.length >= maxLen);
          }
        }
      } else if (prev.type === "mcq" && prev.answer) {
        var radios = frqQuestionsContainer.querySelectorAll('input[name="s2q' + prev.id + '"]');
        radios.forEach(function (r) {
          if (r.value === prev.answer) r.checked = true;
        });
      }
    });
  }

  // --- MCQ Progress ---
  function updateMcqProgress() {
    var answered = 0;
    section1Questions.forEach(function (q) {
      var checked = document.querySelector('input[name="q' + q.id + '"]:checked');
      if (checked) answered++;
    });
    var pct = section1Questions.length > 0
      ? Math.round((answered / section1Questions.length) * 100) : 0;
    progressBar.style.width = pct + "%";
    progressText.textContent = answered + " of " + section1Questions.length + " answered";
  }

  // --- Timer ---
  function startTimer(seconds) {
    secondsRemaining = seconds;
    timerDisplay.style.display = "block";
    updateTimerDisplay();

    timerInterval = setInterval(function () {
      secondsRemaining--;
      if (secondsRemaining <= 0) {
        clearInterval(timerInterval);
        secondsRemaining = 0;
        updateTimerDisplay();
        handleQuizSubmit();
        return;
      }
      updateTimerDisplay();
    }, 1000);
  }

  function updateTimerDisplay() {
    var m = Math.floor(secondsRemaining / 60);
    var s = secondsRemaining % 60;
    timerDisplay.textContent = "Time Remaining: " + pad(m) + ":" + pad(s);
    timerDisplay.classList.toggle("warning", secondsRemaining <= 60 && secondsRemaining > 0);
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  // --- Quiz Submit ---
  async function handleQuizSubmit() {
    // Remove previous warnings
    var existingWarning = document.getElementById("unanswered-warning");
    if (existingWarning) existingWarning.remove();
    mcqQuestionsContainer.querySelectorAll(".unanswered-highlight").forEach(function (el) {
      el.classList.remove("unanswered-highlight");
    });

    // Validate all MCQ answered
    var unanswered = [];
    section1Questions.forEach(function (q) {
      var checked = document.querySelector('input[name="q' + q.id + '"]:checked');
      if (!checked) unanswered.push(q.id);
    });

    if (unanswered.length > 0) {
      var warning = document.createElement("div");
      warning.id = "unanswered-warning";
      warning.className = "unanswered-warning";
      warning.textContent =
        "Please answer all " + section1Questions.length +
        " questions before submitting. You have " + unanswered.length + " unanswered.";
      submitQuizBtn.parentNode.insertBefore(warning, submitQuizBtn);

      unanswered.forEach(function (qid) {
        var card = mcqQuestionsContainer.querySelector('.question-card[data-question-id="' + qid + '"]');
        if (card) card.classList.add("unanswered-highlight");
      });
      var firstCard = mcqQuestionsContainer.querySelector('.question-card[data-question-id="' + unanswered[0] + '"]');
      if (firstCard) firstCard.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    if (timerInterval) clearInterval(timerInterval);

    // Collect MCQ answers
    var mcqAnswers = [];
    var correctAnswers = {};
    section1Questions.forEach(function (q) {
      var checked = document.querySelector('input[name="q' + q.id + '"]:checked');
      var answer = checked ? checked.value : null;
      var isCorrect = answer === q.correctAnswer;
      mcqAnswers.push({
        id: q.id, question: q.question, type: "mcq",
        answer: answer, isCorrect: isCorrect,
      });
      correctAnswers[String(q.id)] = q.correctAnswer;
    });

    // Show result optimistically
    renderMcqResult(mcqAnswers);
    showQuizResult();

    // POST to /submission/quiz
    if (config.apiBaseUrl) {
      try {
        var res = await fetch(config.apiBaseUrl + "/submission/quiz", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: emailInput.value.trim().toLowerCase(),
            submittedAt: new Date().toISOString(),
            mcqAnswers: mcqAnswers,
            correctAnswers: correctAnswers,
          }),
        });
        var data = await res.json();
        if (data.bestScore !== undefined) {
          updateResultBanner(data.mcqScore, data.mcqTotal, data.bestScore, data.mcqAttempts);
        }
      } catch (err) {
        console.error("Failed to submit quiz:", err);
      }
    }
  }

  // --- Render MCQ result ---
  function renderMcqResult(mcqAnswers) {
    var correctCount = mcqAnswers.filter(function (a) { return a.isCorrect; }).length;
    var total = mcqAnswers.length;
    var pct = total > 0 ? Math.round((correctCount / total) * 100) : 0;

    resultScoreBanner.innerHTML =
      '<div class="score-label">Your Score</div>' +
      '<div class="score-value">' + correctCount + " / " + total + "</div>" +
      '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + pct + '%"></div></div>';

    var html = "<h3>Your Answers</h3>";
    mcqAnswers.forEach(function (a, idx) {
      var resultCls = !a.answer ? "unanswered" : a.isCorrect ? "correct" : "incorrect";
      var icon = !a.answer ? "" :
        a.isCorrect ? '<span class="result-icon correct">&#10003;</span>' :
        '<span class="result-icon incorrect">&#10007;</span>';

      var explanationHtml = "";
      if (!a.isCorrect && a.answer) {
        var q = section1Questions.find(function (x) { return x.id === a.id; });
        if (q && q.explanations && q.explanations[a.answer]) {
          explanationHtml =
            '<div class="explanation"><strong>Why this is wrong:</strong> ' +
            escapeHtml(q.explanations[a.answer]) + "</div>";
        }
      }

      html +=
        '<div class="summary-item summary-mcq ' + resultCls + '">' +
        '<div class="summary-question">' + icon + (idx + 1) + ". " + escapeHtml(a.question) + "</div>" +
        '<div class="summary-answer">Your answer: ' + escapeHtml(a.answer || "(no answer)") + "</div>" +
        explanationHtml + "</div>";
    });

    mcqAnswerSummary.innerHTML = html;
  }

  // --- Update result banner with best score ---
  function updateResultBanner(currentScore, currentTotal, bestScore, attemptCount) {
    var bestPct = currentTotal > 0 ? Math.round((bestScore / currentTotal) * 100) : 0;
    var currentPct = currentTotal > 0 ? Math.round((currentScore / currentTotal) * 100) : 0;

    resultScoreBanner.innerHTML =
      '<div class="score-columns">' +
        '<div class="score-column">' +
          '<div class="score-label">This Attempt</div>' +
          '<div class="score-value">' + currentScore + " / " + currentTotal + "</div>" +
          '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + currentPct + '%"></div></div>' +
        "</div>" +
        '<div class="score-column">' +
          '<div class="score-label">Best Score</div>' +
          '<div class="score-value best">' + bestScore + " / " + currentTotal + "</div>" +
          '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + bestPct + '%"></div></div>' +
        "</div>" +
      "</div>" +
      '<div class="attempt-info">Attempt #' + attemptCount + "</div>";
  }

  // --- Save Section 2 Responses ---
  async function handleSaveResponses() {
    var answers = [];
    section2Questions.forEach(function (q) {
      var entry = { id: q.id, question: q.question, type: q.type, answer: null };

      if (q.type === "frq") {
        var ta = frqQuestionsContainer.querySelector('.frq-textarea[data-qid="' + q.id + '"]');
        entry.answer = ta ? ta.value.trim() : null;
      } else if (q.type === "mcq") {
        var checked = frqQuestionsContainer.querySelector('input[name="s2q' + q.id + '"]:checked');
        entry.answer = checked ? checked.value : null;
      }

      answers.push(entry);
    });

    if (config.apiBaseUrl) {
      try {
        saveResponsesBtn.disabled = true;
        saveResponsesBtn.textContent = "Saving...";

        var res = await fetch(config.apiBaseUrl + "/submission/responses", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: emailInput.value.trim().toLowerCase(),
            submittedAt: new Date().toISOString(),
            section2Answers: answers,
          }),
        });

        if (res.ok) {
          showSaveStatus("Responses saved successfully!", "success");
          markTabCompleted("responses");
        } else {
          showSaveStatus("Failed to save. Please try again.", "error");
        }
      } catch (err) {
        console.error("Failed to save responses:", err);
        showSaveStatus("Network error. Please try again.", "error");
      } finally {
        saveResponsesBtn.disabled = false;
        saveResponsesBtn.textContent = "Save Responses";
      }
    }
  }

  function showSaveStatus(message, type) {
    responsesSaveStatus.textContent = message;
    responsesSaveStatus.className = "save-status " + type;
    responsesSaveStatus.style.display = "block";
    setTimeout(function () {
      responsesSaveStatus.style.display = "none";
    }, 3000);
  }

  // --- Tab completion tracking ---
  function markTabCompleted(tabName) {
    tabBtns.forEach(function (btn) {
      if (btn.dataset.tab === tabName) {
        var step = btn.querySelector(".tab-step");
        step.classList.add("completed");
        step.innerHTML = "&#10003;";
      }
    });
  }

  // --- Helpers ---
  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i];
      arr[i] = arr[j];
      arr[j] = tmp;
    }
    return arr;
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function escapeAttr(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  // --- .edu email validation ---
  function isEduEmail(email) {
    return /\.edu$/i.test(email.trim());
  }

  function validateEmail() {
    var val = emailInput.value.trim();
    if (val && !isEduEmail(val)) {
      emailError.style.display = "block";
      emailInput.setCustomValidity("Please enter a valid .edu email address.");
      return false;
    }
    emailError.style.display = "none";
    emailInput.setCustomValidity("");
    return true;
  }

  // --- Events ---
  emailInput.addEventListener("blur", function () {
    if (validateEmail()) {
      lookupUser(emailInput.value);
    }
  });

  emailInput.addEventListener("input", function () {
    validateEmail();
  });

  // Welcome form submit
  infoForm.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!validateEmail()) return;

    // Render section 2 questions immediately
    renderSection2Questions();

    // Pre-fill section 2 if returning user
    if (previousSubmission && previousSubmission.section2Answers) {
      prefillSection2(previousSubmission.section2Answers);
    }

    // Set up quiz landing based on previous submission
    var quizAlreadyDone = previousSubmission && previousSubmission.quizTaken;
    if (quizAlreadyDone) {
      var score = previousSubmission.mcqScore || 0;
      var total = previousSubmission.mcqTotal || 0;
      var attempts = previousSubmission.mcqAttempts || 0;
      showQuizLandingWithScore(score, total, attempts);
      markTabCompleted("quiz");
    } else {
      showQuizLandingFresh();
    }

    // Mark responses tab complete if they have saved answers
    if (previousSubmission && previousSubmission.section2Answers && previousSubmission.section2Answers.length > 0) {
      markTabCompleted("responses");
    }

    // Show tab container - default to Free Response if quiz already done
    showScreen(tabContainer);
    switchTab(quizAlreadyDone ? "responses" : "quiz");
  });

  // Tab switching
  tabBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      switchTab(btn.dataset.tab);
    });
  });

  // Start / retry quiz from landing
  startQuizBtn.addEventListener("click", function () {
    renderSection1Questions();
    updateMcqProgress();
    showQuizActive();
    if (config.timeLimit && config.timeLimit > 0) {
      startTimer(config.timeLimit);
    }
  });

  // Submit quiz
  submitQuizBtn.addEventListener("click", function () {
    handleQuizSubmit();
  });

  // Retry from result screen
  retryQuizBtn.addEventListener("click", function () {
    renderSection1Questions();
    updateMcqProgress();
    showQuizActive();
    if (config.timeLimit && config.timeLimit > 0) {
      startTimer(config.timeLimit);
    }
  });

  // Continue to Free Response from quiz result
  continueToFrqBtn.addEventListener("click", function () {
    switchTab("responses");
  });

  // Save section 2 responses
  saveResponsesBtn.addEventListener("click", function () {
    handleSaveResponses();
  });

  // --- Boot ---
  init();
})();

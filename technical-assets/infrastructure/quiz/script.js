(function () {
  "use strict";

  var config = {};
  var questions = [];
  var section1Questions = [];
  var section2Questions = [];
  var timerInterval = null;
  var secondsRemaining = 0;

  // Returning-user state
  var previousSubmission = null;
  var isRetry = false;
  var currentTab = "quiz";
  var orgKey = "csu";
  var requireEdu = true;

  // Auth state
  var authTokens = null; // { idToken, accessToken, refreshToken }
  var captchaSolved = false;
  var wafScriptsLoaded = false;
  var wafToken = null;
  var resendCooldownInterval = null;

  // DOM elements
  var welcomeScreen = document.getElementById("welcome-screen");
  var otpScreen = document.getElementById("otp-screen");
  var tabContainer = document.getElementById("tab-container");
  var infoForm = document.getElementById("info-form");
  var startBtn = document.getElementById("start-btn");
  var nameInput = document.getElementById("name");
  var emailInput = document.getElementById("email");
  var emailError = document.getElementById("email-error");
  var returningBanner = document.getElementById("returning-user-banner");
  var returningInfo = document.getElementById("returning-user-info");
  var captchaContainer = document.getElementById("captcha-container");
  var captchaError = document.getElementById("captcha-error");

  // OTP elements
  var otpCodeInput = document.getElementById("otp-code");
  var otpEmailDisplay = document.getElementById("otp-email-display");
  var otpError = document.getElementById("otp-error");
  var verifyOtpBtn = document.getElementById("verify-otp-btn");
  var resendOtpBtn = document.getElementById("resend-otp-btn");
  var resendTimer = document.getElementById("resend-timer");
  var otpBackBtn = document.getElementById("otp-back-btn");

  // Tab elements
  var tabBtns = document.querySelectorAll(".tab-btn");
  var tabPanelQuiz = document.getElementById("tab-panel-quiz");
  var tabPanelResponses = document.getElementById("tab-panel-responses");
  var tabPanelFinish = document.getElementById("tab-panel-finish");

  // Quiz tab elements
  var quizLanding = document.getElementById("quiz-landing");
  var quizActive = document.getElementById("quiz-active");
  var quizResult = document.getElementById("quiz-result");
  var startQuizBtn = document.getElementById("start-quiz-btn");
  var submitQuizBtn = document.getElementById("submit-quiz-btn");
  var retryQuizBtn = document.getElementById("retry-quiz-btn");
  var continueToFrqBtn = document.getElementById("continue-to-frq-btn");
  var mcqQuestionsContainer = document.getElementById("mcq-questions-container");
  var mcqAnswerSummary = document.getElementById("mcq-answer-summary");
  var landingScoreBanner = document.getElementById("landing-score-banner");
  var resultScoreBanner = document.getElementById("result-score-banner");
  var quizScoreDisplay = document.getElementById("quiz-score-display");
  var progressBar = document.getElementById("progress-bar");
  var progressText = document.getElementById("progress-text");
  var progressWrapper = document.getElementById("progress-wrapper");
  var timerDisplay = document.getElementById("timer-display");

  // Responses tab elements
  var saveResponsesBtn = document.getElementById("save-responses-btn");
  var frqQuestionsContainer = document.getElementById("frq-questions-container");
  var responsesSaveStatus = document.getElementById("responses-save-status");

  // =========================================================================
  // WAF CAPTCHA
  // =========================================================================

  function loadScript(url) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = url;
      s.onload = resolve;
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  async function initWafCaptcha() {
    if (!config.wafJsUrl || !config.wafCaptchaApiKey) {
      captchaContainer.style.display = "none";
      return;
    }

    try {
      if (!wafScriptsLoaded) {
        await loadScript(config.wafJsUrl + "/jsapi.js");
        wafScriptsLoaded = true;
      }
      renderCaptchaWidget();
    } catch (err) {
      console.warn("WAF CAPTCHA scripts failed to load:", err);
      captchaContainer.style.display = "none";
    }
  }

  function renderCaptchaWidget() {
    captchaContainer.innerHTML = "";
    captchaSolved = false;
    wafToken = null;
    window.AwsWafCaptcha.renderCaptcha(captchaContainer, {
      apiKey: config.wafCaptchaApiKey,
      skipTitle: true,
      onSuccess: function (token) {
        wafToken = token;
        captchaSolved = true;
        hideCaptchaError();
      },
      onError: function (err) {
        console.error("CAPTCHA error:", err);
        captchaSolved = false;
      },
    });
  }

  // Wrapper: adds the WAF token as a header for WAF-protected routes.
  // AwsWafIntegration.fetch() doesn't work cross-origin (API Gateway is a
  // different domain than CloudFront), so we pass the token explicitly.
  function wafFetch(url, options) {
    options = options || {};
    options.headers = options.headers || {};
    if (wafToken) {
      options.headers["x-aws-waf-token"] = wafToken;
    }
    return fetch(url, options);
  }

  // =========================================================================
  // AUTH — tokens
  // =========================================================================

  function _storeTokens(email, tokens) {
    authTokens = tokens;
    localStorage.setItem("quiz_auth_email", email);
    localStorage.setItem("quiz_refresh_token", tokens.refreshToken);
  }

  function _clearTokens() {
    authTokens = null;
    localStorage.removeItem("quiz_auth_email");
    localStorage.removeItem("quiz_refresh_token");
  }

  async function tryRefreshSession() {
    var refreshToken = localStorage.getItem("quiz_refresh_token");
    if (!refreshToken || !config.apiBaseUrl) return false;

    try {
      var res = await fetch(config.apiBaseUrl + "/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken: refreshToken }),
      });
      if (!res.ok) { _clearTokens(); return false; }

      var data = await res.json();
      if (!data.success) { _clearTokens(); return false; }

      authTokens = {
        idToken: data.idToken,
        accessToken: data.accessToken,
        refreshToken: refreshToken,
      };
      return true;
    } catch (err) {
      _clearTokens();
      return false;
    }
  }

  async function authFetch(url, options) {
    if (!authTokens) throw new Error("Not authenticated");

    options = options || {};
    options.headers = options.headers || {};
    options.headers["Authorization"] = "Bearer " + authTokens.idToken;

    var res = await fetch(url, options);

    if (res.status === 401) {
      var refreshed = await tryRefreshSession();
      if (refreshed) {
        options.headers["Authorization"] = "Bearer " + authTokens.idToken;
        res = await fetch(url, options);
      }
    }
    return res;
  }

  // =========================================================================
  // INIT
  // =========================================================================

  async function init() {
    try {
      var results = await Promise.all([
        fetch("config.json"),
        fetch("questions.json"),
      ]);
      config = await results[0].json();
      questions = await results[1].json();
    } catch (err) {
      console.error("Failed to load config or questions:", err);
      document.getElementById("quiz-title").textContent = "Error loading quiz";
      document.getElementById("quiz-description").textContent =
        "Could not load quiz data. Please make sure config.json and questions.json are available.";
      startBtn.disabled = true;
      return;
    }

    // Determine org
    var params = new URLSearchParams(window.location.search);
    var hostMatch = window.location.hostname.match(/quiz\.(csu|ccc)\./i);
    orgKey = params.get("org") || (hostMatch && hostMatch[1].toLowerCase()) || config.defaultOrg || "csu";
    var orgConfig = (config.orgs && config.orgs[orgKey]) || (config.orgs && config.orgs["csu"]) || {};

    config.title = orgConfig.title || config.title || "DxHub Summer Hackathon";
    config.description = orgConfig.description || config.description || "";

    if (orgConfig.logo) {
      document.getElementById("org-logo").src = "logos/" + orgConfig.logo;
    }
    requireEdu = orgConfig.requireEdu !== false;
    if (orgConfig.emailLabel) {
      document.querySelector('label[for="email"]').textContent = orgConfig.emailLabel;
    }
    if (requireEdu) {
      emailInput.setAttribute("pattern", ".+\\.edu$");
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

    // Load WAF CAPTCHA (non-blocking)
    initWafCaptcha();

    // Try restoring session
    var storedEmail = localStorage.getItem("quiz_auth_email");
    if (storedEmail) {
      emailInput.value = storedEmail;
      var storedName = localStorage.getItem("quiz_auth_name");
      if (storedName) nameInput.value = storedName;
      var restored = await tryRefreshSession();
      if (restored) {
        returningBanner.style.display = "block";
        returningInfo.textContent = "Session restored.";
        startBtn.textContent = "Continue";
        captchaSolved = true;
        captchaContainer.style.display = "none";
      }
    }
  }

  // =========================================================================
  // SCREEN NAVIGATION
  // =========================================================================

  function showScreen(screen) {
    [welcomeScreen, otpScreen, tabContainer].forEach(function (s) {
      s.classList.remove("active");
    });
    screen.classList.add("active");
    window.scrollTo(0, 0);
  }

  // =========================================================================
  // AUTH FLOW
  // =========================================================================

  async function handleSendCode(email) {
    if (wafScriptsLoaded && !captchaSolved) {
      showCaptchaError("Please complete the CAPTCHA challenge.");
      return false;
    }

    startBtn.disabled = true;
    startBtn.textContent = "Sending code...";

    try {
      // Use wafFetch so the WAF token is included automatically
      var res = await wafFetch(config.apiBaseUrl + "/auth/send-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email }),
      });
      var data = await res.json();

      if (res.ok && data.success) {
        return true;
      } else {
        showCaptchaError(data.error || "Failed to send verification code.");
        return false;
      }
    } catch (err) {
      showCaptchaError("Network error. Please try again.");
      return false;
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = "Get Started";
    }
  }

  async function handleVerifyCode(email, code) {
    verifyOtpBtn.disabled = true;
    verifyOtpBtn.textContent = "Verifying...";

    try {
      var res = await fetch(config.apiBaseUrl + "/auth/verify-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email, code: code }),
      });
      var data = await res.json();

      if (res.ok && data.success) {
        _storeTokens(email, {
          idToken: data.idToken,
          accessToken: data.accessToken,
          refreshToken: data.refreshToken,
        });
        return true;
      } else {
        showOtpError(data.error || "Verification failed.");
        return false;
      }
    } catch (err) {
      showOtpError("Network error. Please try again.");
      return false;
    } finally {
      verifyOtpBtn.disabled = false;
      verifyOtpBtn.textContent = "Verify";
    }
  }

  async function handleResendCode(email) {
    resendOtpBtn.disabled = true;
    hideOtpError();

    try {
      // WAF token immunity (5 min) should still be valid for resend
      var res = await wafFetch(config.apiBaseUrl + "/auth/send-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email }),
      });
      var data = await res.json();

      if (res.ok) {
        startResendCooldown();
      } else {
        showOtpError(data.error || "Failed to resend code.");
        resendOtpBtn.disabled = false;
      }
    } catch (err) {
      showOtpError("Network error.");
      resendOtpBtn.disabled = false;
    }
  }

  async function proceedAfterAuth() {
    var email = emailInput.value.trim().toLowerCase();

    localStorage.setItem("quiz_auth_name", nameInput.value.trim());

    await lookupUser(email);

    renderSection2Questions();
    if (previousSubmission && previousSubmission.section2Answers) {
      prefillSection2(previousSubmission.section2Answers);
    }

    var quizAlreadyDone = previousSubmission && previousSubmission.quizTaken;
    var frqAlreadyDone = previousSubmission && previousSubmission.section2Answers && previousSubmission.section2Answers.length > 0;

    if (quizAlreadyDone) {
      var score = previousSubmission.mcqScore || 0;
      var total = previousSubmission.mcqTotal || 0;
      var attempts = previousSubmission.mcqAttempts || 0;
      showQuizLandingWithScore(score, total, attempts);
      markTabCompleted("quiz");
      unlockTab("responses");
    } else {
      showQuizLandingFresh();
    }

    if (frqAlreadyDone) {
      markTabCompleted("responses");
    }

    if (quizAlreadyDone && frqAlreadyDone) {
      unlockTab("finish");
      markTabCompleted("finish");
    }

    showScreen(tabContainer);
    if (quizAlreadyDone && frqAlreadyDone) {
      switchTab("finish");
    } else {
      switchTab("quiz");
    }
  }

  // =========================================================================
  // OTP UI helpers
  // =========================================================================

  function showOtpError(msg) {
    otpError.textContent = msg;
    otpError.style.display = "block";
  }

  function hideOtpError() {
    otpError.style.display = "none";
  }

  function showCaptchaError(msg) {
    captchaError.textContent = msg;
    captchaError.style.display = "block";
  }

  function hideCaptchaError() {
    captchaError.style.display = "none";
  }

  function startResendCooldown() {
    var seconds = 30;
    resendOtpBtn.disabled = true;
    resendTimer.textContent = "(" + seconds + "s)";

    if (resendCooldownInterval) clearInterval(resendCooldownInterval);
    resendCooldownInterval = setInterval(function () {
      seconds--;
      if (seconds <= 0) {
        clearInterval(resendCooldownInterval);
        resendOtpBtn.disabled = false;
        resendTimer.textContent = "";
      } else {
        resendTimer.textContent = "(" + seconds + "s)";
      }
    }, 1000);
  }

  // =========================================================================
  // TAB SWITCHING
  // =========================================================================

  function switchTab(tabName) {
    currentTab = tabName;

    tabBtns.forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    tabPanelQuiz.classList.toggle("active", tabName === "quiz");
    tabPanelResponses.classList.toggle("active", tabName === "responses");
    tabPanelFinish.classList.toggle("active", tabName === "finish");

    window.scrollTo(0, 0);
  }

  function unlockTab(tabName) {
    tabBtns.forEach(function (btn) {
      if (btn.dataset.tab === tabName) {
        btn.classList.remove("locked");
      }
    });
  }

  // =========================================================================
  // QUIZ TAB STATE
  // =========================================================================

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

  // =========================================================================
  // USER LOOKUP (authenticated)
  // =========================================================================

  async function lookupUser(email) {
    if (!config.apiBaseUrl || !authTokens) return;

    var trimmed = email.trim().toLowerCase();
    if (!trimmed) return;

    try {
      var res = await authFetch(
        config.apiBaseUrl + "/submission/" + encodeURIComponent(trimmed)
      );
      var data = await res.json();

      if (data.found && data.submission) {
        previousSubmission = data.submission;
        isRetry = true;

        if (previousSubmission.name && !nameInput.value.trim()) {
          nameInput.value = previousSubmission.name;
        }
      } else {
        previousSubmission = null;
        isRetry = false;
      }
    } catch (err) {
      console.warn("Could not look up user:", err);
    }
  }

  // =========================================================================
  // RENDER QUESTIONS
  // =========================================================================

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

  // =========================================================================
  // MCQ PROGRESS + TIMER
  // =========================================================================

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

  // =========================================================================
  // QUIZ SUBMIT
  // =========================================================================

  async function handleQuizSubmit() {
    var existingWarning = document.getElementById("unanswered-warning");
    if (existingWarning) existingWarning.remove();
    mcqQuestionsContainer.querySelectorAll(".unanswered-highlight").forEach(function (el) {
      el.classList.remove("unanswered-highlight");
    });

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

    renderMcqResult(mcqAnswers);
    showQuizResult();
    unlockTab("responses");

    if (config.apiBaseUrl && authTokens) {
      try {
        var res = await authFetch(config.apiBaseUrl + "/submission/quiz", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: emailInput.value.trim().toLowerCase(),
            uni: orgKey,
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

  // =========================================================================
  // MCQ RESULT DISPLAY
  // =========================================================================

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

  // =========================================================================
  // SAVE SECTION 2 RESPONSES
  // =========================================================================

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

    if (config.apiBaseUrl && authTokens) {
      try {
        saveResponsesBtn.disabled = true;
        saveResponsesBtn.textContent = "Saving...";

        var res = await authFetch(config.apiBaseUrl + "/submission/responses", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: emailInput.value.trim().toLowerCase(),
            uni: orgKey,
            submittedAt: new Date().toISOString(),
            section2Answers: answers,
          }),
        });

        if (res.ok) {
          showSaveStatus("Responses saved successfully!", "success");
          markTabCompleted("responses");
          unlockTab("finish");
          markTabCompleted("finish");
          switchTab("finish");
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

  // =========================================================================
  // TAB COMPLETION
  // =========================================================================

  function markTabCompleted(tabName) {
    tabBtns.forEach(function (btn) {
      if (btn.dataset.tab === tabName) {
        var step = btn.querySelector(".tab-step");
        step.classList.add("completed");
        step.innerHTML = "&#10003;";
      }
    });
  }

  // =========================================================================
  // HELPERS
  // =========================================================================

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

  function isEduEmail(email) {
    return /\.edu$/i.test(email.trim());
  }

  function validateEmail() {
    var val = emailInput.value.trim();
    if (requireEdu && val && !isEduEmail(val)) {
      emailError.style.display = "block";
      emailInput.setCustomValidity("Please enter a valid .edu email address.");
      return false;
    }
    emailError.style.display = "none";
    emailInput.setCustomValidity("");
    return true;
  }

  // =========================================================================
  // EVENT LISTENERS
  // =========================================================================

  emailInput.addEventListener("blur", function () {
    validateEmail();
  });

  emailInput.addEventListener("input", function () {
    validateEmail();
    // If user changes email away from the restored session email,
    // clear auth state and re-show CAPTCHA so they go through OTP again.
    var storedEmail = localStorage.getItem("quiz_auth_email");
    if (storedEmail && emailInput.value.trim().toLowerCase() !== storedEmail) {
      _clearTokens();
      captchaSolved = false;
      wafToken = null;
      returningBanner.style.display = "none";
      startBtn.textContent = "Get Started";
      if (wafScriptsLoaded) {
        captchaContainer.style.display = "";
        renderCaptchaWidget();
      }
    }
  });

  otpCodeInput.addEventListener("input", function () {
    var val = otpCodeInput.value.replace(/[^0-9]/g, "");
    otpCodeInput.value = val;
    verifyOtpBtn.disabled = val.length !== 6;
  });

  // Welcome form submit
  infoForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    if (!validateEmail()) return;
    hideCaptchaError();

    var email = emailInput.value.trim().toLowerCase();

    // Already authenticated for this email — skip OTP
    var storedEmail = localStorage.getItem("quiz_auth_email");
    if (authTokens && storedEmail === email) {
      await proceedAfterAuth();
      return;
    }

    // Send verification code (WAF validates CAPTCHA before it reaches Lambda)
    var sent = await handleSendCode(email);
    if (sent) {
      otpEmailDisplay.textContent = email;
      otpCodeInput.value = "";
      verifyOtpBtn.disabled = true;
      hideOtpError();
      showScreen(otpScreen);
      otpCodeInput.focus();
      startResendCooldown();
    }
  });

  // Verify OTP
  verifyOtpBtn.addEventListener("click", async function () {
    var email = emailInput.value.trim().toLowerCase();
    var code = otpCodeInput.value.trim();

    if (code.length !== 6) {
      showOtpError("Please enter the 6-digit code.");
      return;
    }

    var success = await handleVerifyCode(email, code);
    if (success) {
      await proceedAfterAuth();
    }
  });

  // Resend OTP
  resendOtpBtn.addEventListener("click", function () {
    handleResendCode(emailInput.value.trim().toLowerCase());
  });

  // Back from OTP screen
  otpBackBtn.addEventListener("click", function () {
    if (resendCooldownInterval) clearInterval(resendCooldownInterval);
    if (wafScriptsLoaded) renderCaptchaWidget();
    showScreen(welcomeScreen);
  });

  // Tab switching
  tabBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (btn.classList.contains("locked")) return;
      switchTab(btn.dataset.tab);
    });
  });

  startQuizBtn.addEventListener("click", function () {
    renderSection1Questions();
    updateMcqProgress();
    showQuizActive();
    if (config.timeLimit && config.timeLimit > 0) {
      startTimer(config.timeLimit);
    }
  });

  submitQuizBtn.addEventListener("click", function () {
    handleQuizSubmit();
  });

  retryQuizBtn.addEventListener("click", function () {
    renderSection1Questions();
    updateMcqProgress();
    showQuizActive();
    if (config.timeLimit && config.timeLimit > 0) {
      startTimer(config.timeLimit);
    }
  });

  continueToFrqBtn.addEventListener("click", function () {
    switchTab("responses");
  });

  saveResponsesBtn.addEventListener("click", function () {
    handleSaveResponses();
  });

  // =========================================================================
  // BOOT
  // =========================================================================

  init();
})();

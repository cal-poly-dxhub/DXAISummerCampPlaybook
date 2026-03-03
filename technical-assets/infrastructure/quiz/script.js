(function () {
  "use strict";

  let config = {};
  let questions = [];
  let timerInterval = null;
  let secondsRemaining = 0;

  // Returning-user state
  let previousSubmission = null;
  let isRetry = false;

  // DOM elements
  const welcomeScreen = document.getElementById("welcome-screen");
  const quizScreen = document.getElementById("quiz-screen");
  const submissionScreen = document.getElementById("submission-screen");
  const infoForm = document.getElementById("info-form");
  const startBtn = document.getElementById("start-btn");
  const submitBtn = document.getElementById("submit-btn");
  const questionsContainer = document.getElementById("questions-container");
  const progressBar = document.getElementById("progress-bar");
  const progressText = document.getElementById("progress-text");
  const progressWrapper = document.getElementById("progress-wrapper");
  const timerDisplay = document.getElementById("timer-display");
  const answerSummary = document.getElementById("answer-summary");
  const returningBanner = document.getElementById("returning-user-banner");
  const returningInfo = document.getElementById("returning-user-info");
  const bestScoreInfo = document.getElementById("best-score-info");
  const emailInput = document.getElementById("email");
  const nameInput = document.getElementById("name");

  // --- Init ---
  async function init() {
    try {
      const [configRes, questionsRes] = await Promise.all([
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

    document.getElementById("header-title").textContent = config.title || "";
    document.getElementById("quiz-title").textContent = config.title || "Quiz";
    document.getElementById("quiz-description").textContent =
      config.description || "";

    if (!config.showProgressBar) {
      progressWrapper.style.display = "none";
    }
  }

  // --- Screen navigation ---
  function showScreen(screen) {
    [welcomeScreen, quizScreen, submissionScreen].forEach(function (s) {
      s.classList.remove("active");
    });
    screen.classList.add("active");
    window.scrollTo(0, 0);
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

        // Pre-fill name if available
        if (previousSubmission.name && !nameInput.value.trim()) {
          nameInput.value = previousSubmission.name;
        }

        // Show banner
        var attempts = previousSubmission.attemptCount || 1;
        var score = previousSubmission.mcqScore || 0;
        var total = previousSubmission.mcqTotal || 0;
        returningInfo.textContent =
          "You have " + attempts + " previous attempt" +
          (attempts !== 1 ? "s" : "") +
          ". Best MCQ score: " + score + "/" + total + ".";
        returningBanner.style.display = "block";
        startBtn.textContent = "Retry Quiz";
      } else {
        previousSubmission = null;
        isRetry = false;
        returningBanner.style.display = "none";
        startBtn.textContent = "Start Quiz";
      }
    } catch (err) {
      console.warn("Could not look up user:", err);
    }
  }

  // --- Render questions ---
  function renderQuestions() {
    var list = config.shuffleQuestions ? shuffle(questions.slice()) : questions;

    list.forEach(function (q, idx) {
      var card = document.createElement("div");
      card.className = "question-card";
      card.dataset.questionId = q.id;

      var typeBadge =
        q.type === "mcq"
          ? '<span class="question-type-badge mcq">Multiple Choice</span>'
          : '<span class="question-type-badge frq">Free Response</span>';

      var inner =
        '<div class="question-number">Question ' +
        (idx + 1) +
        " of " +
        list.length +
        "</div>" +
        typeBadge +
        '<div class="question-text">' +
        escapeHtml(q.question) +
        "</div>";

      if (q.type === "mcq") {
        var shuffledOptions = shuffle(q.options.slice());
        inner += '<ul class="options-list">';
        shuffledOptions.forEach(function (opt, oi) {
          var inputId = "q" + q.id + "_opt" + oi;
          inner +=
            "<li>" +
            '<label for="' +
            inputId +
            '">' +
            '<input type="radio" id="' +
            inputId +
            '" name="q' +
            q.id +
            '" value="' +
            escapeAttr(opt) +
            '">' +
            "<span>" +
            escapeHtml(opt) +
            "</span>" +
            "</label>" +
            "</li>";
        });
        inner += "</ul>";
      } else if (q.type === "frq") {
        var maxLen = q.maxLength || 1000;
        inner +=
          '<textarea class="frq-textarea" data-qid="' +
          q.id +
          '" maxlength="' +
          maxLen +
          '" placeholder="Type your answer here…"></textarea>' +
          '<div class="char-count" id="cc-' +
          q.id +
          '">0 / ' +
          maxLen +
          "</div>";
      }

      card.innerHTML = inner;
      questionsContainer.appendChild(card);
    });

    // Attach char count listeners
    questionsContainer.querySelectorAll(".frq-textarea").forEach(function (ta) {
      var qid = ta.dataset.qid;
      var q = questions.find(function (x) {
        return String(x.id) === qid;
      });
      var maxLen = (q && q.maxLength) || 1000;
      ta.addEventListener("input", function () {
        var cc = document.getElementById("cc-" + qid);
        cc.textContent = ta.value.length + " / " + maxLen;
        cc.classList.toggle("over", ta.value.length >= maxLen);
        updateProgress();
      });
    });

    // Update progress on radio change
    questionsContainer.querySelectorAll('input[type="radio"]').forEach(function (r) {
      r.addEventListener("change", updateProgress);
    });

    // Pre-fill FRQ answers on retry
    if (isRetry && previousSubmission && previousSubmission.answers) {
      previousSubmission.answers.forEach(function (prev) {
        if (prev.type === "frq" && prev.answer) {
          var ta = document.querySelector('.frq-textarea[data-qid="' + prev.id + '"]');
          if (ta) {
            ta.value = prev.answer;
            // Update char count
            var q = questions.find(function (x) { return x.id === prev.id; });
            var maxLen = (q && q.maxLength) || 1000;
            var cc = document.getElementById("cc-" + prev.id);
            if (cc) {
              cc.textContent = prev.answer.length + " / " + maxLen;
              cc.classList.toggle("over", prev.answer.length >= maxLen);
            }
          }
        }
      });
    }
  }

  // --- Progress ---
  function updateProgress() {
    var answered = 0;
    questions.forEach(function (q) {
      if (q.type === "mcq") {
        var checked = document.querySelector('input[name="q' + q.id + '"]:checked');
        if (checked) answered++;
      } else if (q.type === "frq") {
        var ta = document.querySelector('.frq-textarea[data-qid="' + q.id + '"]');
        if (ta && ta.value.trim().length > 0) answered++;
      }
    });
    var pct = questions.length > 0 ? Math.round((answered / questions.length) * 100) : 0;
    progressBar.style.width = pct + "%";
    progressText.textContent = answered + " of " + questions.length + " answered";
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
        handleSubmit();
        return;
      }
      updateTimerDisplay();
    }, 1000);
  }

  function updateTimerDisplay() {
    var m = Math.floor(secondsRemaining / 60);
    var s = secondsRemaining % 60;
    timerDisplay.textContent =
      "Time Remaining: " + pad(m) + ":" + pad(s);
    timerDisplay.classList.toggle("warning", secondsRemaining <= 60 && secondsRemaining > 0);
  }

  function pad(n) {
    return n < 10 ? "0" + n : String(n);
  }

  // --- Collect answers ---
  function collectAnswers() {
    var answers = [];
    var correctAnswers = {};

    questions.forEach(function (q) {
      var entry = { id: q.id, question: q.question, type: q.type, answer: null };

      if (q.type === "mcq") {
        var checked = document.querySelector('input[name="q' + q.id + '"]:checked');
        entry.answer = checked ? checked.value : null;
        entry.isCorrect = entry.answer === q.correctAnswer;
        // Store correct answer in separate map for server-side grading
        correctAnswers[String(q.id)] = q.correctAnswer;
      } else if (q.type === "frq") {
        var ta = document.querySelector('.frq-textarea[data-qid="' + q.id + '"]');
        entry.answer = ta ? ta.value.trim() : null;
      }

      answers.push(entry);
    });

    return { answers: answers, correctAnswers: correctAnswers };
  }

  // --- Validate all questions answered ---
  function validateAllAnswered() {
    var unanswered = [];
    questions.forEach(function (q) {
      if (q.type === "mcq") {
        var checked = document.querySelector('input[name="q' + q.id + '"]:checked');
        if (!checked) unanswered.push(q.id);
      } else if (q.type === "frq") {
        var ta = document.querySelector('.frq-textarea[data-qid="' + q.id + '"]');
        if (!ta || !ta.value.trim()) unanswered.push(q.id);
      }
    });
    return unanswered;
  }

  // --- Submit ---
  async function handleSubmit() {
    // Remove any previous warning
    var existingWarning = document.getElementById("unanswered-warning");
    if (existingWarning) existingWarning.remove();
    questionsContainer.querySelectorAll(".unanswered-highlight").forEach(function (el) {
      el.classList.remove("unanswered-highlight");
    });

    // Validate
    var unanswered = validateAllAnswered();
    if (unanswered.length > 0) {
      // Show warning
      var warning = document.createElement("div");
      warning.id = "unanswered-warning";
      warning.className = "unanswered-warning";
      warning.textContent = "Please answer all " + questions.length + " questions before submitting. You have " + unanswered.length + " unanswered.";
      submitBtn.parentNode.insertBefore(warning, submitBtn);

      // Highlight unanswered cards and scroll to first
      unanswered.forEach(function (qid) {
        var card = document.querySelector('.question-card[data-question-id="' + qid + '"]');
        if (card) card.classList.add("unanswered-highlight");
      });
      var firstCard = document.querySelector('.question-card[data-question-id="' + unanswered[0] + '"]');
      if (firstCard) firstCard.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }

    if (timerInterval) clearInterval(timerInterval);

    var name = nameInput.value.trim();
    var email = emailInput.value.trim();
    var collected = collectAnswers();
    var answers = collected.answers;
    var correctAnswers = collected.correctAnswers;

    var submission = {
      name: name,
      email: email,
      submittedAt: new Date().toISOString(),
      answers: answers,
      correctAnswers: correctAnswers,
    };

    // Show submission screen immediately (optimistic UI)
    renderSummary(answers);
    showScreen(submissionScreen);

    // POST to API if configured
    if (config.apiBaseUrl) {
      try {
        var res = await fetch(config.apiBaseUrl + "/submission", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(submission),
        });
        var data = await res.json();

        // Update score banner with best score and attempt count
        if (data.bestScore !== undefined) {
          updateScoreBanner(
            data.mcqScore, data.mcqTotal,
            data.bestScore, data.bestTotal,
            data.attemptCount
          );
        }
      } catch (err) {
        console.error("Failed to submit to API:", err);
      }
    } else {
      console.log("=== Quiz Submission ===");
      console.log(JSON.stringify(submission, null, 2));
    }
  }

  // --- Update score banner with best score side-by-side ---
  function updateScoreBanner(currentScore, currentTotal, bestScore, bestTotal, attemptCount) {
    var banner = document.getElementById("score-banner");
    if (!banner) return;

    var bestPct = bestTotal > 0 ? Math.round((bestScore / bestTotal) * 100) : 0;
    var currentPct = currentTotal > 0 ? Math.round((currentScore / currentTotal) * 100) : 0;

    var html =
      '<div class="score-columns">' +
        '<div class="score-column">' +
          '<div class="score-label">This Attempt</div>' +
          '<div class="score-value">' + currentScore + " / " + currentTotal + "</div>" +
          '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + currentPct + '%"></div></div>' +
        "</div>" +
        '<div class="score-column">' +
          '<div class="score-label">Best Score</div>' +
          '<div class="score-value best">' + bestScore + " / " + bestTotal + "</div>" +
          '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + bestPct + '%"></div></div>' +
        "</div>" +
      "</div>" +
      '<div class="attempt-info">Attempt #' + attemptCount + "</div>" +
      '<div class="attempt-info">Your free-response answers have been saved.</div>' +
      '<div class="mt-2"><button class="btn btn-gold" id="retry-btn">Retry Quiz</button></div>';

    banner.innerHTML = html;

    // Re-attach retry handler
    document.getElementById("retry-btn").addEventListener("click", handleRetry);

    // Hide the separate best-score-info div since it's now inline
    bestScoreInfo.style.display = "none";
  }

  // --- Render summary ---
  function renderSummary(answers) {
    var mcqAnswers = answers.filter(function (a) { return a.type === "mcq"; });
    var correctCount = mcqAnswers.filter(function (a) { return a.isCorrect; }).length;
    var totalMcq = mcqAnswers.length;
    var pct = totalMcq > 0 ? Math.round((correctCount / totalMcq) * 100) : 0;

    // Score banner — starts as single column, updated to side-by-side when API responds
    var html =
      '<div class="score-banner" id="score-banner">' +
      '<div class="score-label">Multiple Choice Score</div>' +
      '<div class="score-value">' + correctCount + " / " + totalMcq + "</div>" +
      '<div class="score-bar-track"><div class="score-bar-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="mt-2"><button class="btn btn-gold" id="retry-btn">Retry Quiz</button></div>' +
      "</div>";

    html += "<h3>Your Answers</h3>";
    answers.forEach(function (a, idx) {
      var answerText = a.answer || "(no answer)";
      var num = (idx + 1) + ". ";

      if (a.type === "mcq") {
        var resultCls = !a.answer ? "unanswered" : a.isCorrect ? "correct" : "incorrect";
        var icon = !a.answer ? "" : a.isCorrect ? '<span class="result-icon correct">&#10003;</span>' : '<span class="result-icon incorrect">&#10007;</span>';

        var explanationHtml = "";
        if (!a.isCorrect && a.answer) {
          var q = questions.find(function (x) { return x.id === a.id; });
          if (q && q.explanations && q.explanations[a.answer]) {
            explanationHtml =
              '<div class="explanation">' +
              '<strong>Why this is wrong:</strong> ' + escapeHtml(q.explanations[a.answer]) +
              "</div>";
          }
        }

        html +=
          '<div class="summary-item summary-mcq ' + resultCls + '">' +
          '<div class="summary-question">' + icon + num + escapeHtml(a.question) + "</div>" +
          '<div class="summary-answer">Your answer: ' + escapeHtml(answerText) + "</div>" +
          explanationHtml +
          "</div>";
      } else {
        var cls = a.answer ? "summary-answer" : "summary-answer unanswered";
        html +=
          '<div class="summary-item">' +
          '<div class="summary-question">' + num + escapeHtml(a.question) + "</div>" +
          '<div class="' + cls + '">' + escapeHtml(answerText) + "</div>" +
          "</div>";
      }
    });
    answerSummary.innerHTML = html;

    // Attach retry button handler
    document.getElementById("retry-btn").addEventListener("click", handleRetry);
  }

  // --- Retry quiz ---
  function handleRetry() {
    // Store current answers as previous submission for FRQ pre-fill
    var collected = collectAnswers();
    previousSubmission = { answers: collected.answers };
    isRetry = true;

    // Clear quiz container and re-render
    questionsContainer.innerHTML = "";
    renderQuestions();
    updateProgress();
    showScreen(quizScreen);

    if (config.timeLimit && config.timeLimit > 0) {
      startTimer(config.timeLimit);
    }
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
  var emailError = document.getElementById("email-error");

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

  infoForm.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!validateEmail()) return;
    renderQuestions();
    updateProgress();
    showScreen(quizScreen);

    if (config.timeLimit && config.timeLimit > 0) {
      startTimer(config.timeLimit);
    }
  });

  submitBtn.addEventListener("click", function () {
    handleSubmit();
  });

  // --- Boot ---
  init();
})();

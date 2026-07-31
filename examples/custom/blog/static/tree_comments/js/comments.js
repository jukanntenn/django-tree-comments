/* ==========================================================================
   django-tree-comments · example · progressive enhancement script (dependency-free vanilla JS)
   Modules:
     1. Avatar generation (initial + deterministic color)
     2. Relative time (naturaltime style, client-side rendering)
     3. Anchor highlight + smooth scrolling (lands on #c{pk} or "reply to @who" click)
     4. Character counter
     5. Sorting (newest/oldest, client-side DOM reordering)
     6. Collapse/expand + "N replies" badge
     7. "Show more replies" virtualization
   ========================================================================== */

(function () {
  "use strict";

  var CONFIG = {
    autoCollapseDepth: 6,     // Collapse subtrees deeper than this
    maxVisibleReplies: 3,     // Max direct child comments shown per node; the rest collapse into "show more"
  };

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $all(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  /* ===== 1. Avatar ===== */
  var AVATAR_COLORS = 8;
  function hashCode(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
    return Math.abs(hash);
  }
  function getInitial(name) {
    if (!name) return "?";
    var trimmed = String(name).trim();
    if (!trimmed) return "?";
    if (/[\u4e00-\u9fff]/.test(trimmed)) return trimmed.charAt(trimmed.length - 1); // CJK: take the last character
    return trimmed.charAt(0);
  }
  function paintAvatar(el) {
    var name = el.getAttribute("data-name") || "";
    var idx = hashCode(name || "?") % AVATAR_COLORS + 1;
    el.textContent = getInitial(name);
    el.style.setProperty("--tc-avatar-bg", "var(--tc-avatar-" + idx + "-bg)");
    el.style.setProperty("--tc-avatar-fg", "var(--tc-avatar-" + idx + "-fg)");
  }
  function paintAllAvatars(root) {
    $all(".tc-avatar:not([data-painted])", root).forEach(function (el) {
      paintAvatar(el); el.setAttribute("data-painted", "true");
    });
  }

  /* ===== 2. Relative time ===== */
  function relativeTime(iso) {
    var then = new Date(iso);
    if (isNaN(then.getTime())) return "";
    var now = new Date();
    var sec = Math.round((now - then) / 1000);
    var future = sec < 0; sec = Math.abs(sec);
    var units = [
      { s: 60, name: "second" }, { s: 3600, name: "minute" },
      { s: 86400, name: "hour" }, { s: 604800, name: "day" },
      { s: 2629800, name: "week" }, { s: 31557600, name: "month" }, { s: Infinity, name: "year" },
    ];
    var divisor = 1, unit = "second";
    for (var i = 0; i < units.length; i++) {
      if (sec < units[i].s) { unit = units[i].name; break; }
      divisor = units[i].s;
    }
    var value = Math.max(1, Math.floor(sec / divisor));
    function pluralize(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }
    if (sec < 60) return future ? "in a few seconds" : "just now";
    var str = pluralize(value, unit);
    return future ? "in " + str : str + " ago";
  }
  function paintAllTimes(root) {
    $all("time.tc-date[data-iso]", root).forEach(function (el) {
      var iso = el.getAttribute("data-iso");
      if (!iso) return;
      var label = relativeTime(iso);
      if (label) el.textContent = label;
    });
  }

  /* ===== 3. Anchor highlight + smooth scrolling ===== */
  function highlightComment(commentEl) {
    if (!commentEl) return;
    commentEl.scrollIntoView({ behavior: "smooth", block: "center" });
    commentEl.classList.remove("is-target");
    void commentEl.offsetWidth;
    commentEl.classList.add("is-target");
    setTimeout(function () { commentEl.classList.remove("is-target"); }, 2500);
  }
  function scrollToComment(pk) {
    var target = document.getElementById("c" + pk);
    if (target) highlightComment(target);
  }
  function handleAnchor() {
    var hash = window.location.hash;
    if (hash && hash.indexOf("#c") === 0) {
      setTimeout(function () { scrollToComment(hash.slice(2)); }, 100);
    }
  }
  function bindReplyLinks(root) {
    $all(".tc-reply-to__link", root).forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        var pk = link.getAttribute("data-parent-id");
        if (pk) scrollToComment(pk);
      });
    });
  }

  /* ===== 4. Character counter ===== */
  function bindCharCount(form) {
    var textarea = form.querySelector("textarea[name='comment']");
    var counter = form.querySelector("[data-charcount]");
    if (!textarea || !counter) return;
    var max = parseInt(counter.getAttribute("data-maxlength"), 10) || 3000;
    function update() {
      var len = textarea.value.length;
      counter.textContent = len + " / " + max;
      counter.classList.remove("tc-charcount--warn", "tc-charcount--danger");
      if (len > max) counter.classList.add("tc-charcount--danger");
      else if (len > max * 0.9) counter.classList.add("tc-charcount--warn");
    }
    textarea.addEventListener("input", update);
    update();
  }

  /* ===== 5. Sorting ===== */
  function bindSort(app) {
    var thread = app.querySelector("#comments-threaded");
    if (!thread) return;
    var sortBtns = $all(".tc-sort-btn", app);
    sortBtns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var order = btn.getAttribute("data-order");
        sortBtns.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        btn.setAttribute("aria-pressed", "true");
        var roots = $all(":scope > .tc-comment", thread);
        roots.sort(function (a, b) {
          var da = a.getAttribute("data-submit-date") || "";
          var db = b.getAttribute("data-submit-date") || "";
          return order === "newest" ? db.localeCompare(da) : da.localeCompare(db);
        });
        roots.forEach(function (r) { thread.appendChild(r); });
      });
    });
  }

  /* ===== 6. Collapse/expand ===== */
  function countDescendants(commentEl) {
    return $all(".tc-comment", commentEl.querySelector(":scope > .tc-children")).length;
  }
  function setCollapsed(commentEl, collapsed) {
    commentEl.setAttribute("data-collapsed", collapsed ? "true" : "false");
    var pill = commentEl.querySelector(":scope > .tc-collapsed-pill");
    if (pill) {
      var n = countDescendants(commentEl);
      pill.querySelector(".tc-collapsed-pill__count").textContent = n;
    }
  }
  function bindCollapse(commentEl) {
    var pill = commentEl.querySelector(":scope > .tc-collapsed-pill");
    if (pill) pill.addEventListener("click", function () {
      setCollapsed(commentEl, commentEl.getAttribute("data-collapsed") !== "true");
    });
  }
  function autoCollapseDeep(app) {
    $all(".tc-comment", app).forEach(function (el) {
      var depth = parseInt(el.getAttribute("data-depth"), 10) || 0;
      if (depth >= CONFIG.autoCollapseDepth) setCollapsed(el, true);
      bindCollapse(el);
    });
  }

  /* ===== 7. "Show more replies" virtualization ===== */
  function virtualizeReplies(commentEl) {
    var children = commentEl.querySelector(":scope > .tc-children");
    if (!children) return;
    var direct = $all(":scope > .tc-comment", children);
    if (direct.length <= CONFIG.maxVisibleReplies) return;
    var hidden = direct.slice(CONFIG.maxVisibleReplies);
    hidden.forEach(function (c) { c.classList.add("tc-reply--hidden"); });
    var moreBtn = document.createElement("button");
    moreBtn.type = "button";
    moreBtn.className = "tc-show-more-replies";
    var n = hidden.length;
    moreBtn.textContent = "Show " + n + " more replies";
    moreBtn.addEventListener("click", function () {
      hidden.forEach(function (c) { c.classList.remove("tc-reply--hidden"); });
      moreBtn.remove();
    });
    children.appendChild(moreBtn);
  }
  function virtualizeAll(app) { $all(".tc-comment", app).forEach(virtualizeReplies); }

  /* ===== Initialization ===== */
  function enhance(root) {
    paintAllAvatars(root);
    paintAllTimes(root);
    bindReplyLinks(root);
    $all("form[id='comment-form'], form.tc-composer", root).forEach(bindCharCount);
  }
  function initApp(app) {
    enhance(app);
    bindSort(app);
    autoCollapseDeep(app);
    virtualizeAll(app);
  }
  ready(function () {
    $all(".tc-tree-comments").forEach(initApp);
    handleAnchor();
    document.body.addEventListener("htmx:afterSwap", function (e) {
      var target = e.detail && e.detail.target;
      if (target) enhance(target);
    });
  });

  window.TreeComments = { relativeTime: relativeTime, getInitial: getInitial };
})();

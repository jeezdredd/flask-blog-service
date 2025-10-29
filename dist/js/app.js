const state = {
  apiKey: "",
  tweets: [],
  pagination: null,
  currentUser: null,
  sort: "popular",
  limit: 10,
  page: 1,
  toastTimer: null,
};

const STORAGE_KEY = "microblog.apiKey";

const elements = {
  apiKeySelect: document.getElementById("api-key-select"),
  apiKeyInput: document.getElementById("api-key-input"),
  applyApiKey: document.getElementById("apply-api-key"),
  refreshButton: document.getElementById("refresh-feed"),
  sortSelect: document.getElementById("sort-select"),
  limitSelect: document.getElementById("limit-select"),
  composeForm: document.getElementById("compose-form"),
  composeText: document.getElementById("compose-text"),
  composeFile: document.getElementById("compose-file"),
  composeFileName: document.getElementById("compose-file-name"),
  feedList: document.getElementById("feed"),
  prevPage: document.getElementById("prev-page"),
  nextPage: document.getElementById("next-page"),
  pageIndicator: document.getElementById("page-indicator"),
  toast: document.getElementById("toast"),
  currentUserName: document.getElementById("current-user-name"),
  currentUserFollowers: document.getElementById("current-user-followers-count"),
  currentUserFollowing: document.getElementById("current-user-following-count"),
  followingList: document.getElementById("following-list"),
  statUsers: document.getElementById("stat-users"),
  statTweets: document.getElementById("stat-tweets"),
  statLikes: document.getElementById("stat-likes"),
  popularAuthors: document.getElementById("popular-authors"),
  trendingTweets: document.getElementById("trending-tweets"),
};

function showToast(message, type = "info") {
  const toast = elements.toast;
  if (!toast) {
    return;
  }
  toast.textContent = message;
  if (type && type !== "info") {
    toast.dataset.type = type;
  } else {
    delete toast.dataset.type;
  }
  toast.classList.add("visible");
  if (state.toastTimer) {
    window.clearTimeout(state.toastTimer);
  }
  state.toastTimer = window.setTimeout(() => {
    toast.classList.remove("visible");
  }, 4000);
}

function updateSelectForKey(key) {
  if (!elements.apiKeySelect) {
    return;
  }
  if (["test", "alice", "bob"].includes(key)) {
    elements.apiKeySelect.value = key;
  } else {
    elements.apiKeySelect.value = "custom";
  }
}

function setApiKey(key, { persist = true, refresh = true } = {}) {
  state.apiKey = (key || "").trim();
  if (elements.apiKeyInput) {
    elements.apiKeyInput.value = state.apiKey;
  }
  if (persist) {
    try {
      localStorage.setItem(STORAGE_KEY, state.apiKey);
    } catch (error) {
      console.warn("Unable to persist API key", error);
    }
  }
  updateSelectForKey(state.apiKey);
  if (refresh && state.apiKey) {
    refreshEverything({ resetPage: true });
  }
}

function formatDate(value) {
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return "";
    }
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  } catch (error) {
    return "";
  }
}

function truncate(value, limit = 90) {
  if (!value) {
    return "";
  }
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, limit - 3)}...`;
}

function applyLocalLikeState(tweetId, shouldBeLiked) {
  if (!Array.isArray(state.tweets) || !state.tweets.length) {
    return;
  }

  const tweet = state.tweets.find((item) => Number(item.id) === Number(tweetId));
  if (!tweet) {
    return;
  }

  const alreadyLiked = Boolean(tweet.liked_by_me);
  if (alreadyLiked === shouldBeLiked) {
    return;
  }

  const delta = shouldBeLiked ? 1 : -1;
  const currentCount = Number.isFinite(tweet.likes_count) ? Number(tweet.likes_count) : Number(tweet.likes?.length || 0);
  tweet.likes_count = Math.max(0, currentCount + delta);
  tweet.liked_by_me = shouldBeLiked;

  const currentUser = state.currentUser;
  const likesArray = Array.isArray(tweet.likes) ? [...tweet.likes] : [];

  if (currentUser) {
    const existingIndex = likesArray.findIndex((like) => like.user_id === currentUser.id);
    if (shouldBeLiked) {
      if (existingIndex === -1) {
        likesArray.unshift({ user_id: currentUser.id, name: currentUser.name });
      }
    } else if (existingIndex !== -1) {
      likesArray.splice(existingIndex, 1);
    }
  }

  tweet.likes = likesArray;
}

async function request(path, { method = "GET", json, formData } = {}) {
  const headers = {};
  if (state.apiKey) {
    headers["api-key"] = state.apiKey;
  }

  let body;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (formData) {
    body = formData;
  }

  const response = await fetch(path, { method, headers, body });
  const contentType = response.headers.get("content-type") || "";
  let payload = null;
  if (contentType.includes("application/json")) {
    payload = await response.json();
  } else if (contentType.includes("text/")) {
    payload = await response.text();
  }

  if (!response.ok) {
    const message = payload && payload.error_message
      ? payload.error_message
      : payload && payload.detail
        ? payload.detail
        : response.statusText;
    throw new Error(message || "Request failed");
  }

  if (payload && payload.result === false) {
    throw new Error(payload.error_message || "Request failed");
  }

  return payload;
}

async function loadCurrentUser() {
  const data = await request("/api/users/me");
  state.currentUser = data.user;
  renderCurrentUser(state.currentUser);
}

function renderCurrentUser(user) {
  if (!elements.currentUserName) {
    return;
  }
  if (!user) {
    elements.currentUserName.textContent = "Unknown member";
    elements.currentUserFollowers.textContent = "0";
    elements.currentUserFollowing.textContent = "0";
    if (elements.followingList) {
      elements.followingList.innerHTML = "";
    }
    return;
  }

  elements.currentUserName.textContent = user.name;
  elements.currentUserFollowers.textContent = String(user.followers.length);
  elements.currentUserFollowing.textContent = String(user.following.length);

  if (elements.followingList) {
    elements.followingList.innerHTML = "";
    if (user.following.length === 0) {
      const chip = document.createElement("span");
      chip.className = "chip muted";
      chip.textContent = "Not following anyone yet";
      elements.followingList.appendChild(chip);
    } else {
      user.following.slice(0, 6).forEach((followee) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = followee.name;
        elements.followingList.appendChild(chip);
      });
      if (user.following.length > 6) {
        const more = document.createElement("span");
        more.className = "chip muted";
        more.textContent = `+${user.following.length - 6}`;
        elements.followingList.appendChild(more);
      }
    }
  }
}

async function loadDashboard() {
  const data = await request("/api/dashboard");
  renderDashboard(data.stats);
}

function renderDashboard(stats) {
  if (!stats) {
    return;
  }
  if (elements.statUsers) {
    elements.statUsers.textContent = Number(stats.total_users || 0).toLocaleString();
  }
  if (elements.statTweets) {
    elements.statTweets.textContent = Number(stats.total_tweets || 0).toLocaleString();
  }
  if (elements.statLikes) {
    elements.statLikes.textContent = Number(stats.total_likes || 0).toLocaleString();
  }

  if (elements.popularAuthors) {
    elements.popularAuthors.innerHTML = "";
    if (stats.popular_authors && stats.popular_authors.length) {
      stats.popular_authors.forEach((author) => {
        const item = document.createElement("li");
        item.className = "pill";

        const title = document.createElement("div");
        title.className = "pill-title";
        title.textContent = author.name;

        const meta = document.createElement("div");
        meta.className = "pill-meta";
        meta.textContent = `${author.followers_count} followers • ${author.tweet_count} updates`;

        item.appendChild(title);
        item.appendChild(meta);
        elements.popularAuthors.appendChild(item);
      });
    } else {
      const empty = document.createElement("li");
      empty.className = "pill";
      empty.textContent = "No authors yet";
      elements.popularAuthors.appendChild(empty);
    }
  }

  if (elements.trendingTweets) {
    elements.trendingTweets.innerHTML = "";
    if (stats.trending_tweets && stats.trending_tweets.length) {
      stats.trending_tweets.forEach((tweet) => {
        const item = document.createElement("li");
        item.className = "pill";

        const title = document.createElement("div");
        title.className = "pill-title";
        title.textContent = tweet.author;

        const meta = document.createElement("div");
        meta.className = "pill-meta";
        meta.textContent = truncate(tweet.content, 100);

        const likes = document.createElement("div");
        likes.className = "pill-meta";
        likes.textContent = `${tweet.likes_count} likes`;

        item.appendChild(title);
        item.appendChild(meta);
        item.appendChild(likes);
        elements.trendingTweets.appendChild(item);
      });
    } else {
      const empty = document.createElement("li");
      empty.className = "pill";
      empty.textContent = "No trending posts";
      elements.trendingTweets.appendChild(empty);
    }
  }
}

async function loadFeed({ resetPage = false } = {}) {
  if (resetPage) {
    state.page = 1;
  }

  const params = new URLSearchParams({
    sort: state.sort,
    page: String(state.page),
    limit: String(state.limit),
  });

  const data = await request(`/api/tweets?${params.toString()}`);
  state.tweets = Array.isArray(data.tweets) ? data.tweets : [];
  state.pagination = data.pagination || null;

  if (state.pagination) {
    state.page = state.pagination.page || state.page;
    state.limit = state.pagination.limit || state.limit;
  }

  renderFeed();
  updatePaginationControls();
}

function renderFeed() {
  if (!elements.feedList) {
    return;
  }

  elements.feedList.innerHTML = "";
  if (!state.tweets.length) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No updates yet. Share the first one!";
    elements.feedList.appendChild(empty);
    return;
  }

  state.tweets.forEach((tweet) => {
    const item = document.createElement("li");
    item.className = "tweet-card";
    item.dataset.tweetId = String(tweet.id);

    const header = document.createElement("div");
    header.className = "tweet-header";

    const author = document.createElement("div");
    author.className = "tweet-author";
    author.textContent = tweet.author.name;

    const meta = document.createElement("div");
    meta.className = "tweet-meta";
    meta.textContent = formatDate(tweet.stamp);

    header.appendChild(author);
    header.appendChild(meta);
    item.appendChild(header);

    const body = document.createElement("p");
    body.className = "tweet-body";
    body.textContent = tweet.content;
    item.appendChild(body);

    if (Array.isArray(tweet.attachments) && tweet.attachments.length) {
      const attachments = document.createElement("div");
      attachments.className = "attachments";
      tweet.attachments.forEach((src) => {
        const image = document.createElement("img");
        image.src = src;
        image.alt = "Attachment";
        attachments.appendChild(image);
      });
      item.appendChild(attachments);
    }

    const likesToShow = Array.isArray(tweet.likes) ? tweet.likes.slice(0, 6) : [];
    if (likesToShow.length) {
      const likesList = document.createElement("div");
      likesList.className = "likes-list";
      likesToShow.forEach((like) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = like.name || `User ${like.user_id}`;
        likesList.appendChild(chip);
      });
      const remainingLikes = Math.max(0, Number(tweet.likes_count || likesToShow.length) - likesToShow.length);
      if (remainingLikes > 0) {
        const more = document.createElement("span");
        more.className = "chip muted";
        more.textContent = `+${remainingLikes}`;
        likesList.appendChild(more);
      }
      item.appendChild(likesList);
    }

    const footer = document.createElement("div");
    footer.className = "tweet-footer";

    const likeButton = document.createElement("button");
    likeButton.type = "button";
    likeButton.className = "button secondary like-button";
    likeButton.dataset.action = "toggle-like";
    likeButton.dataset.liked = String(Boolean(tweet.liked_by_me));
    const likeCount = Number(tweet.likes_count || 0);
    const likeIcon = document.createElement("img");
    likeIcon.src = "/favicon.ico";
    likeIcon.alt = "Like";
    likeIcon.className = "like-icon";
    likeButton.appendChild(likeIcon);
    const likeText = document.createElement("span");
    likeText.textContent = likeCount === 0 ? "Like" : likeCount === 1 ? "1 like" : `${likeCount} likes`;
    likeButton.appendChild(likeText);
    if (likeCount === 1) {
      likeButton.classList.add("one-like");
    }
    likeButton.setAttribute("aria-pressed", tweet.liked_by_me ? "true" : "false");
    if (tweet.liked_by_me) {
      likeButton.classList.add("is-active");
      likeButton.title = "Unlike";
    } else {
      likeButton.title = "Like";
    }
    footer.appendChild(likeButton);

    if (state.currentUser && tweet.author.id === state.currentUser.id) {
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "button ghost danger";
      deleteButton.dataset.action = "delete-tweet";
      deleteButton.textContent = "Delete";
      footer.appendChild(deleteButton);
    }

    item.appendChild(footer);
    elements.feedList.appendChild(item);
  });
}

function updatePaginationControls() {
  const pagination = state.pagination || {};
  const page = pagination.page || state.page || 1;
  const hasNext = Boolean(pagination.has_next);
  const hasPrevious = Boolean(pagination.has_previous);

  if (elements.pageIndicator) {
    elements.pageIndicator.textContent = `Page ${page}`;
  }
  if (elements.prevPage) {
    elements.prevPage.disabled = !hasPrevious;
  }
  if (elements.nextPage) {
    elements.nextPage.disabled = !hasNext;
  }
  if (elements.limitSelect) {
    elements.limitSelect.value = String(state.limit);
  }
  if (elements.sortSelect) {
    elements.sortSelect.value = state.sort;
  }
}

async function handleCompose(event) {
  event.preventDefault();
  if (!state.apiKey) {
    showToast("Set an API key before posting", "error");
    return;
  }

  const text = elements.composeText.value.trim();
  if (!text) {
    showToast("Message cannot be empty", "error");
    return;
  }

  try {
    let mediaIds = [];
    const file = elements.composeFile.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file, file.name || "upload");
      const upload = await request("/api/medias", { method: "POST", formData });
      mediaIds = upload.media_id ? [upload.media_id] : [];
    }

    const payload = {
      tweet_data: text,
    };
    if (mediaIds.length) {
      payload.tweet_media_ids = mediaIds;
    }

    await request("/api/tweets", { method: "POST", json: payload });
    elements.composeForm.reset();
    if (elements.composeFileName) {
      elements.composeFileName.textContent = "No file selected";
    }
    showToast("Update published", "success");
    await Promise.all([
      loadFeed({ resetPage: true }),
      loadDashboard(),
    ]);
  } catch (error) {
    showToast(error.message || "Could not publish update", "error");
  }
}

async function handleLike(tweetId, liked, triggerButton) {
  if (!state.apiKey) {
    showToast("Set an API key first", "error");
    return;
  }
  if (triggerButton) {
    triggerButton.disabled = true;
  }
  try {
    if (liked) {
      await request(`/api/tweets/${tweetId}/likes`, { method: "DELETE" });
      applyLocalLikeState(tweetId, false);
    } else {
      await request(`/api/tweets/${tweetId}/likes`, { method: "POST" });
      applyLocalLikeState(tweetId, true);
    }
    renderFeed();
    updatePaginationControls();
    loadDashboard().catch((error) => {
      console.warn("Failed to refresh dashboard after like", error);
    });
  } catch (error) {
    showToast(error.message || "Could not update like", "error");
  } finally {
    if (triggerButton) {
      triggerButton.disabled = false;
    }
  }
}

async function handleDelete(tweetId) {
  if (!state.apiKey) {
    showToast("Set an API key first", "error");
    return;
  }
  if (!window.confirm("Delete this update?")) {
    return;
  }
  try {
    await request(`/api/tweets/${tweetId}`, { method: "DELETE" });
    showToast("Update removed", "success");
    await Promise.all([
      loadFeed({ resetPage: state.tweets.length === 1 }),
      loadDashboard(),
    ]);
  } catch (error) {
    showToast(error.message || "Could not delete update", "error");
  }
}

function handleFeedClick(event) {
  const button = event.target.closest("[data-action]");
  if (!button) {
    return;
  }
  const container = button.closest("[data-tweet-id]");
  if (!container) {
    return;
  }
  const tweetId = Number(container.dataset.tweetId);
  if (!tweetId) {
    return;
  }
  const action = button.dataset.action;
  if (action === "toggle-like") {
    const liked = button.dataset.liked === "true";
    handleLike(tweetId, liked, button);
    return;
  } else if (action === "delete-tweet") {
    handleDelete(tweetId);
  }
}

function bindEvents() {
  if (elements.applyApiKey) {
    elements.applyApiKey.addEventListener("click", () => setApiKey(elements.apiKeyInput.value));
  }

  if (elements.apiKeyInput) {
    elements.apiKeyInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        setApiKey(elements.apiKeyInput.value);
      }
    });
  }

  if (elements.apiKeySelect) {
    elements.apiKeySelect.addEventListener("change", (event) => {
      const value = event.target.value;
      if (value === "custom") {
        if (elements.apiKeyInput) {
          elements.apiKeyInput.focus();
        }
        return;
      }
      setApiKey(value);
    });
  }

  if (elements.refreshButton) {
    elements.refreshButton.addEventListener("click", () => refreshEverything({ resetPage: true }));
  }

  if (elements.sortSelect) {
    elements.sortSelect.addEventListener("change", () => {
      state.sort = elements.sortSelect.value;
      loadFeed({ resetPage: true }).catch((error) => {
        showToast(error.message || "Could not load feed", "error");
      });
    });
  }

  if (elements.limitSelect) {
    elements.limitSelect.addEventListener("change", () => {
      const value = Number(elements.limitSelect.value);
      state.limit = Number.isFinite(value) && value > 0 ? value : 10;
      loadFeed({ resetPage: true }).catch((error) => {
        showToast(error.message || "Could not load feed", "error");
      });
    });
  }

  if (elements.composeForm) {
    elements.composeForm.addEventListener("submit", handleCompose);
  }

  if (elements.composeFile) {
    elements.composeFile.addEventListener("change", () => {
      const file = elements.composeFile.files[0];
      if (elements.composeFileName) {
        elements.composeFileName.textContent = file ? file.name : "No file selected";
      }
    });
  }

  if (elements.feedList) {
    elements.feedList.addEventListener("click", handleFeedClick);
  }

  if (elements.prevPage) {
    elements.prevPage.addEventListener("click", () => {
      if (state.page > 1) {
        state.page -= 1;
        loadFeed().catch((error) => {
          showToast(error.message || "Could not load feed", "error");
        });
      }
    });
  }

  if (elements.nextPage) {
    elements.nextPage.addEventListener("click", () => {
      if (state.pagination && state.pagination.has_next) {
        state.page += 1;
        loadFeed().catch((error) => {
          showToast(error.message || "Could not load feed", "error");
        });
      }
    });
  }

  if (elements.toast) {
    elements.toast.addEventListener("click", () => {
      elements.toast.classList.remove("visible");
    });
  }
}

async function refreshEverything({ resetPage = false } = {}) {
  if (!state.apiKey) {
    showToast("Provide an API key to load data", "error");
    return;
  }
  try {
    await loadCurrentUser();
    await loadDashboard();
    await loadFeed({ resetPage });
  } catch (error) {
    showToast(error.message || "Unable to load data", "error");
  }
}

function init() {
  bindEvents();
  const savedKey = (() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || "test";
    } catch (error) {
      return "test";
    }
  })();

  state.sort = elements.sortSelect ? elements.sortSelect.value : "popular";
  state.limit = elements.limitSelect ? Number(elements.limitSelect.value) || 10 : 10;

  setApiKey(savedKey, { persist: false, refresh: false });
  updateSelectForKey(state.apiKey);
  if (state.apiKey) {
    refreshEverything({ resetPage: true });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

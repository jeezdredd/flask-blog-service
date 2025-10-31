const state = {
  apiKey: "",
  currentUser: null,
  profileUser: null,
  userId: null,
  followers: [],
  following: [],
  activeTab: "followers",
};

const STORAGE_KEY = "microblog.apiKey";

const elements = {
  profileCover: document.getElementById("profile-cover"),
  profileAvatar: document.getElementById("profile-avatar"),
  profileName: document.getElementById("profile-name"),
  profileFollowingCount: document.getElementById("profile-following-count"),
  profileFollowersCount: document.getElementById("profile-followers-count"),
  profileActions: document.getElementById("profile-actions"),
  followersGrid: document.getElementById("followers-grid"),
  followingGrid: document.getElementById("following-grid"),
  toast: document.getElementById("toast"),
};

function showToast(message, type = "info") {
  const toast = elements.toast;
  if (!toast) return;

  toast.textContent = message;
  if (type && type !== "info") {
    toast.setAttribute("data-type", type);
  } else {
    toast.removeAttribute("data-type");
  }

  toast.classList.add("visible");
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    toast.classList.remove("visible");
  }, 3000);
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (state.apiKey) {
    headers["api-key"] = state.apiKey;
  }

  const response = await fetch(path, {
    ...options,
    headers,
  });

  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    if (payload && typeof payload === "object") {
      if (payload.detail) {
        if (typeof payload.detail === "string") {
          message = payload.detail;
        } else if (Array.isArray(payload.detail)) {
          message = payload.detail.map(d => d.msg || JSON.stringify(d)).join(", ");
        }
      }
    }
    throw new Error(message);
  }

  if (payload && payload.result === false) {
    throw new Error(payload.error_message || "Request failed");
  }

  return payload;
}

function getUserIdFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("id");
}

async function loadCurrentUser() {
  try {
    const data = await request("/api/users/me");
    state.currentUser = data.user;
  } catch (error) {
    console.error("Failed to load current user:", error);
  }
}

async function loadProfile() {
  if (!state.userId) {
    showToast("No user ID provided", "error");
    return;
  }

  try {
    const data = await request(`/api/users/${state.userId}`);
    state.profileUser = data.user;
    renderProfile();
  } catch (error) {
    showToast(error.message || "Failed to load profile", "error");
  }
}

async function loadFollowers() {
  if (!state.userId) return;

  try {
    const data = await request(`/api/users/${state.userId}/followers`);
    state.followers = data.followers || [];
    renderFollowers();
  } catch (error) {
    showToast(error.message || "Failed to load followers", "error");
  }
}

async function loadFollowing() {
  if (!state.userId) return;

  try {
    const data = await request(`/api/users/${state.userId}/following`);
    state.following = data.following || [];
    renderFollowing();
  } catch (error) {
    showToast(error.message || "Failed to load following", "error");
  }
}

function renderProfile() {
  if (!state.profileUser) return;

  const user = state.profileUser;
  const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

  elements.profileAvatar.textContent = initials;
  elements.profileName.textContent = user.name;
  elements.profileFollowersCount.textContent = user.followers?.length || 0;
  elements.profileFollowingCount.textContent = user.following?.length || 0;

  const isMe = state.currentUser && state.currentUser.id === user.id;
  const isFollowing = state.currentUser && user.followers?.some(f => f.id === state.currentUser.id);

  elements.profileActions.innerHTML = "";

  if (!isMe) {
    const followButton = document.createElement("button");
    followButton.type = "button";
    followButton.className = isFollowing ? "button secondary" : "button primary";
    followButton.textContent = isFollowing ? "Unfollow" : "Follow";
    followButton.addEventListener("click", () => handleFollowToggle(isFollowing));
    elements.profileActions.appendChild(followButton);
  }
}

function renderFollowers() {
  if (!elements.followersGrid) return;

  elements.followersGrid.innerHTML = "";

  if (state.followers.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "No followers yet";
    elements.followersGrid.appendChild(empty);
    return;
  }

  state.followers.forEach(follower => {
    const card = createUserCard(follower);
    elements.followersGrid.appendChild(card);
  });
}

function renderFollowing() {
  if (!elements.followingGrid) return;

  elements.followingGrid.innerHTML = "";

  if (state.following.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "Not following anyone yet";
    elements.followingGrid.appendChild(empty);
    return;
  }

  state.following.forEach(followee => {
    const card = createUserCard(followee);
    elements.followingGrid.appendChild(card);
  });
}

function createUserCard(user) {
  const card = document.createElement("div");
  card.className = "user-card-mini";

  const avatar = document.createElement("div");
  avatar.className = "user-card-avatar";
  const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  avatar.textContent = initials;

  const name = document.createElement("div");
  name.className = "user-card-name";
  name.textContent = user.name;

  const link = document.createElement("a");
  link.href = `/profile.html?id=${user.id}`;
  link.className = "user-card-link";
  link.textContent = "View profile";

  card.appendChild(avatar);
  card.appendChild(name);
  card.appendChild(link);

  return card;
}

async function handleFollowToggle(isCurrentlyFollowing) {
  if (!state.apiKey) {
    showToast("Please sign in first", "error");
    return;
  }

  try {
    if (isCurrentlyFollowing) {
      await request(`/api/users/${state.userId}/follow`, { method: "DELETE" });
      showToast("Unfollowed successfully", "success");
    } else {
      await request(`/api/users/${state.userId}/follow`, { method: "POST" });
      showToast("Followed successfully", "success");
    }

    await Promise.all([loadProfile(), loadFollowers()]);
  } catch (error) {
    showToast(error.message || "Failed to update follow status", "error");
  }
}

function bindEvents() {
  const tabButtons = document.querySelectorAll(".tab-button");
  tabButtons.forEach(button => {
    button.addEventListener("click", () => {
      const tab = button.getAttribute("data-tab");
      state.activeTab = tab;

      tabButtons.forEach(b => b.classList.remove("active"));
      button.classList.add("active");

      document.querySelectorAll(".tab-content").forEach(content => {
        content.classList.remove("active");
      });
      document.getElementById(`tab-${tab}`).classList.add("active");

      if (tab === "followers" && state.followers.length === 0) {
        loadFollowers();
      } else if (tab === "following" && state.following.length === 0) {
        loadFollowing();
      }
    });
  });
}

async function init() {
  console.log("Profile page initializing...");
  console.log("Current URL:", window.location.href);

  const debugUrl = document.getElementById("debug-url");
  const debugKey = document.getElementById("debug-key");
  const debugStatus = document.getElementById("debug-status");

  if (debugUrl) debugUrl.textContent = "URL: " + window.location.href;

  const savedKey = localStorage.getItem(STORAGE_KEY);
  console.log("API Key found:", !!savedKey);
  console.log("API Key value:", savedKey ? savedKey.substring(0, 5) + "..." : "null");

  if (debugKey) debugKey.textContent = "API Key: " + (savedKey ? "Found" : "Not found");

  if (!savedKey) {
    console.log("No API key, showing error...");
    showToast("Please sign in first", "error");
    elements.profileName.textContent = "Please sign in first";
    if (debugStatus) debugStatus.textContent = "Status: No API key - please sign in on home page first";
    return;
  }

  state.apiKey = savedKey;

  state.userId = getUserIdFromURL();
  console.log("User ID from URL:", state.userId);

  if (!state.userId) {
    console.log("No user ID provided, showing error...");
    showToast("No user ID provided", "error");
    elements.profileName.textContent = "No user ID provided";
    if (debugStatus) debugStatus.textContent = "Status: No user ID in URL";
    return;
  }

  if (debugStatus) debugStatus.textContent = "Status: Loading profile for user #" + state.userId;

  bindEvents();

  try {
    console.log("Loading profile data...");
    await loadCurrentUser();
    console.log("Current user loaded:", state.currentUser?.name);
    await loadProfile();
    console.log("Profile loaded:", state.profileUser?.name);
    await loadFollowers();
    console.log("Followers loaded:", state.followers.length);
    if (debugStatus) debugStatus.textContent = "Status: Profile loaded successfully!";
  } catch (error) {
    console.error("Initialization error:", error);
    showToast("Failed to load profile: " + error.message, "error");
    if (debugStatus) debugStatus.textContent = "Status: Error: " + error.message;
  }
}

console.log("Profile.js loaded");

window.addEventListener('load', () => {
  console.log("Window loaded event fired");
});

document.addEventListener('DOMContentLoaded', () => {
  console.log("DOMContentLoaded event fired");
});

init();


// A temporary browser client. Firebase owns sign-in; the API owns account access.
const $ = (id) => document.getElementById(id);
let auth;
let account = null;
let busy = false;
let signingIn = false;
let generation = 0;
let savedRecipes = [];
let nextRecipeOffset = null;
let editingRecipe = null;
let createRequestId = null;

function status(message, error = false) {
  $("status").textContent = message;
  $("status").dataset.error = String(error);
}

function controls() {
  const locked = busy || signingIn;
  $("signin").disabled = !auth || locked || Boolean(auth.currentUser);
  $("signout").disabled = !auth?.currentUser || locked;
  $("reload").disabled = !auth?.currentUser || locked;
  $("profile-fields").disabled = !account || locked;
  $("kitchen-fields").disabled = !account || locked;
  $("library-fields").disabled = !account || locked;
  $("recipe-fields").disabled = !account || locked;
}

function showAccount(value) {
  account = value;
  $("account-output").textContent = value ? JSON.stringify(value, null, 2) : "Sign in to load your account.";
  $("profile-form").reset();
  $("kitchen-form").reset();
  if (value) {
    $("first-name").value = value.profile.first_name;
    $("last-name").value = value.profile.last_name;
    $("household").value = value.profile.household_size;
    $("minutes").value = value.profile.default_cooking_minutes;
    $("measurements").value = value.profile.measurement_system;
    $("owned").value = Object.keys(value.kitchen.appliances).filter((id) => value.kitchen.appliances[id]).join(", ");
    $("not-owned").value = Object.keys(value.kitchen.appliances).filter((id) => !value.kitchen.appliances[id]).join(", ");
    $("spices").value = value.kitchen.spices.join(", ");
    $("spice-setup").value = value.kitchen.spice_setup;
  }
  controls();
}

function explain(error) {
  const messages = {
    "auth/unauthorized-domain": "Add localhost to Firebase Authentication → Settings → Authorized domains, then reopen this page using localhost.",
    "auth/operation-not-allowed": "Enable Google in Firebase Authentication → Sign-in method.",
    "auth/configuration-not-found": "Initialize Firebase Authentication in the console, then enable Google sign-in.",
    "auth/popup-blocked": "Allow the Google sign-in popup for this local page, then try again.",
    "auth/popup-closed-by-user": "The sign-in window was closed. You can try again.",
  };
  return messages[error.code] || error.message || "The request failed. Check the server log.";
}

async function api(path, method = "GET", body) {
  const user = auth.currentUser;
  if (!user) throw new Error("Sign in first.");
  // Tokens stay inside the SDK/request header; never print, display, or copy them.
  const token = await user.getIdToken();
  const response = await fetch(path, {
    method, cache: "no-store",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail :
      Array.isArray(data.detail) ? data.detail.map((item) => `${item.loc.join(".")}: ${item.msg}`).join("; ") :
      "Check the input fields against the API schema.";
    const conflict = response.status === 409 ? " Your unsaved fields are still here. Copy your edits before reloading saved data." : "";
    throw new Error(`${response.status}: ${detail}${conflict} Request ID: ${response.headers.get("X-Request-ID") || "unavailable"}`);
  }
  return data;
}

async function operation(action) {
  if (busy || signingIn) return;
  busy = true;
  controls();
  try { await action(); } catch (error) {
    status(explain(error), true);
    if (!$("recipe-editor").hidden) $("recipe-status").textContent = explain(error);
  }
  finally { busy = false; controls(); }
}

const list = (value) => [...new Set(value.split(",").map((item) => item.trim()).filter(Boolean))];

$("profile-form").addEventListener("submit", (event) => {
  event.preventDefault();
  operation(async () => {
    const value = await api("/api/v1/account/profile", "PUT", {
      expected_revision: account.revision,
      // PUT replaces a section, so retain fields this helper doesn't expose.
      profile: { ...account.profile,
        first_name: $("first-name").value, last_name: $("last-name").value,
        household_size: Number($("household").value),
        default_cooking_minutes: Number($("minutes").value),
        measurement_system: $("measurements").value,
      },
    });
    showAccount(value);
    status(`Profile saved to MongoDB. Account revision ${value.revision}.`);
  });
});

$("kitchen-form").addEventListener("submit", (event) => {
  event.preventDefault();
  operation(async () => {
    const owned = list($("owned").value);
    const notOwned = list($("not-owned").value);
    if (owned.some((id) => notOwned.includes(id))) throw new Error("An appliance cannot be in both lists.");
    const value = await api("/api/v1/account/kitchen", "PUT", {
      expected_revision: account.revision,
      kitchen: { ...account.kitchen,
        appliances: Object.fromEntries([...owned.map((id) => [id, true]), ...notOwned.map((id) => [id, false])]),
        spices: list($("spices").value), spice_setup: $("spice-setup").value,
      },
    });
    showAccount(value);
    status(`Kitchen saved to MongoDB. Account revision ${value.revision}.`);
  });
});

$("reload").addEventListener("click", () => operation(async () => {
  if (account && !window.confirm("Reload saved data? Unsaved form edits will be replaced.")) return;
  showAccount(await api("/api/v1/account"));
  status(`Loaded saved data from MongoDB. Account revision ${account.revision}.`);
}));

async function initialize() {
  try {
    const response = await fetch("/dev/firebase-config", { cache: "no-store" });
    const config = await response.json();
    if (!response.ok) throw new Error(config.detail);
    const [{ initializeApp }, sdk] = await Promise.all([
      import("https://www.gstatic.com/firebasejs/13.4.0/firebase-app.js"),
      import("https://www.gstatic.com/firebasejs/13.4.0/firebase-auth.js"),
    ]);
    auth = sdk.getAuth(initializeApp(config));
    // This helper intentionally forgets the browser login on page close/reload.
    await sdk.setPersistence(auth, sdk.inMemoryPersistence);
    $("signin").addEventListener("click", () => {
      if (busy || signingIn) return;
      signingIn = true;
      controls();
      // Start directly from the click so browsers permit the popup.
      sdk.signInWithPopup(auth, new sdk.GoogleAuthProvider())
        .catch((error) => status(explain(error), true))
        .finally(() => { signingIn = false; controls(); });
    });
    $("signout").addEventListener("click", () => operation(async () => {
      await sdk.signOut(auth);
    }));
    sdk.onAuthStateChanged(auth, async (user) => {
      const version = ++generation;
      showAccount(null);
      savedRecipes = [];
      nextRecipeOffset = null;
      renderRecipes();
      resetRecipeEditor();
      $("identity").textContent = user ? `Signed in as ${user.email || user.displayName || "Google user"}.` : "Not signed in.";
      if (!user) { status("Ready. Continue with Google to connect your kitchen."); return; }
      busy = true;
      controls();
      status("Google sign-in succeeded. Verifying identity and loading your account…");
      try {
        const value = await api("/api/v1/account", "POST");
        if (version !== generation) return;
        showAccount(value);
        status(`Account loaded from MongoDB. Revision ${value.revision}. You can save your profile and kitchen.`);
        await loadRecipes();
      } catch (error) {
        if (version === generation) status(explain(error), true);
      } finally {
        if (version === generation) { busy = false; controls(); }
      }
    });
    controls();
  } catch (error) {
    status(`${explain(error)} If Firebase scripts cannot load, check your internet connection.`, true);
  }
}

initialize();

function inputLabel(text, input) {
  const label = document.createElement("label");
  label.append(document.createTextNode(text), input);
  return label;
}

function addIngredient(value = {}) {
  const row = document.createElement("fieldset");
  row.className = "ingredient-row";
  row.baseIngredient = value;
  const legend = document.createElement("legend");
  legend.textContent = "Ingredient";
  row.append(legend);
  for (const [key, title, type] of [
    ["name", "Ingredient name", "text"], ["original_text", "Original ingredient wording", "text"],
    ["quantity", "Numeric quantity (optional)", "number"],
  ]) {
    const input = document.createElement("input");
    input.type = type;
    input.dataset.field = key;
    input.value = value[key] ?? "";
    input.required = key !== "quantity";
    if (type === "number") { input.min = "0"; input.step = "any"; }
    row.append(inputLabel(title, input));
  }
  const unit = document.createElement("select");
  unit.dataset.field = "unit";
  for (const name of ["", "g", "kg", "oz", "lb", "ml", "l", "tsp", "tbsp", "cup", "count"]) {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name || "No unit / to taste";
    unit.append(option);
  }
  unit.value = value.unit ?? "";
  row.append(inputLabel("Unit", unit));
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "secondary";
  remove.textContent = "Remove ingredient";
  remove.addEventListener("click", () => row.remove());
  row.append(remove);
  $("recipe-ingredients").append(row);
}

function resetRecipeEditor() {
  editingRecipe = null;
  createRequestId = null;
  $("recipe-form").reset();
  $("recipe-ingredients").replaceChildren();
  $("recipe-editor").hidden = true;
  $("recipe-status").textContent = "";
}

function openRecipeEditor(record = null) {
  resetRecipeEditor();
  editingRecipe = record;
  createRequestId = crypto.randomUUID();
  $("recipe-editor").hidden = false;
  $("recipe-editor-title").textContent = record ? "Edit your private recipe" : "Add a private recipe";
  const recipe = record?.recipe;
  if (recipe) {
    for (const [id, field] of [
      ["recipe-title", "title"], ["recipe-description", "description"], ["recipe-servings", "servings"],
      ["recipe-prep", "prep_minutes"], ["recipe-cook", "cook_minutes"], ["recipe-cuisine", "cuisine"],
      ["recipe-cost", "estimated_cost"], ["recipe-currency", "currency"], ["recipe-source", "source_url"],
    ]) $(id).value = recipe[field] ?? "";
    $("recipe-image").value = recipe.image_urls[0] || "";
    $("recipe-steps").value = recipe.steps.join("\n");
    $("recipe-equipment").value = recipe.equipment.join(", ");
    recipe.ingredients.forEach(addIngredient);
  } else {
    $("recipe-servings").value = account?.profile.household_size || 2;
    addIngredient();
  }
  $("recipe-title").focus();
}

function renderRecipes() {
  $("recipe-list").replaceChildren();
  $("library-status").textContent = !account ? "Sign in to load your recipes." :
    savedRecipes.length ? `${savedRecipes.length} private recipe(s) loaded.` : "No private recipes yet. Add your first recipe.";
  $("more-recipes").hidden = nextRecipeOffset === null;
  for (const record of savedRecipes) {
    const card = document.createElement("article");
    card.className = "recipe-card";
    if (record.recipe.image_urls[0]) {
      const photo = document.createElement("img");
      photo.src = record.recipe.image_urls[0];
      photo.alt = record.recipe.title;
      photo.loading = "lazy";
      photo.referrerPolicy = "no-referrer";
      photo.addEventListener("error", () => photo.remove());
      card.append(photo);
    }
    const heading = document.createElement("h3");
    heading.textContent = record.recipe.title;
    const info = document.createElement("p");
    info.textContent = `${record.recipe.servings} servings · ${record.recipe.prep_minutes + record.recipe.cook_minutes} min prep + cook · Private`;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary";
    button.textContent = "View / edit recipe";
    button.addEventListener("click", () => operation(async () => {
      if (!confirmCloseRecipe()) return;
      const latest = await api(`/api/v1/recipes/${record.id}`);
      openRecipeEditor(latest);
    }));
    card.append(heading, info, button);
    $("recipe-list").append(card);
  }
}

async function loadRecipes(append = false) {
  const offset = append ? nextRecipeOffset : 0;
  if (offset === null) return;
  const page = await api(`/api/v1/recipes?offset=${offset}&limit=20`);
  savedRecipes = append ? [...savedRecipes, ...page.items] : page.items;
  nextRecipeOffset = page.next_offset;
  renderRecipes();
}

function confirmCloseRecipe() {
  return $("recipe-editor").hidden || window.confirm("Close this editor? Unsaved recipe edits will be discarded.");
}

$("new-recipe").addEventListener("click", () => {
  if (confirmCloseRecipe()) openRecipeEditor();
});
$("cancel-recipe").addEventListener("click", () => {
  if (confirmCloseRecipe()) resetRecipeEditor();
});
$("add-ingredient").addEventListener("click", () => addIngredient());
$("reload-recipes").addEventListener("click", () => operation(() => loadRecipes()));
$("more-recipes").addEventListener("click", () => operation(() => loadRecipes(true)));

$("recipe-form").addEventListener("submit", (event) => {
  event.preventDefault();
  operation(async () => {
    const ingredients = [...$("recipe-ingredients").querySelectorAll(".ingredient-row")].map((row) => {
      const get = (field) => row.querySelector(`[data-field="${field}"]`).value;
      return { ...row.baseIngredient, name: get("name"), original_text: get("original_text"),
        quantity: get("quantity") || null, unit: get("unit") || null };
    });
    const recipe = { ...(editingRecipe?.recipe || {}),
      title: $("recipe-title").value, description: $("recipe-description").value,
      servings: Number($("recipe-servings").value), prep_minutes: Number($("recipe-prep").value),
      cook_minutes: Number($("recipe-cook").value), ingredients,
      steps: $("recipe-steps").value.split("\n").filter((step) => step.trim()),
      equipment: list($("recipe-equipment").value), cuisine: $("recipe-cuisine").value,
      source_url: $("recipe-source").value || null,
      image_urls: [$("recipe-image").value, ...(editingRecipe?.recipe.image_urls.slice(1) || [])].filter(Boolean),
      estimated_cost: $("recipe-cost").value || null, currency: $("recipe-currency").value,
      visibility: "private",
    };
    $("recipe-status").textContent = "Saving your private recipe…";
    const record = editingRecipe ? await api(`/api/v1/recipes/${editingRecipe.id}`, "PUT", {
      expected_revision: editingRecipe.revision, recipe,
    }) : await api("/api/v1/recipes", "POST", {client_request_id: createRequestId, recipe});
    // Keep this saved identity even if refreshing the list subsequently fails.
    editingRecipe = record;
    $("recipe-editor-title").textContent = "Edit your private recipe";
    $("recipe-status").textContent = `Saved privately to MongoDB. Recipe revision ${record.revision}.`;
    status(`Saved “${record.recipe.title}” to your private recipe library.`);
    await loadRecipes();
  });
});

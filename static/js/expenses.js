(function () {
  const root = document.getElementById("budget-page-root");
  if (!root) return;

  const currency = root.dataset.currency || "USD";
  const proposeUrl = root.dataset.proposeUrl;
  const applyUrl = root.dataset.applyUrl;

  const toggleBudgetBtn = document.getElementById("btn-toggle-budget-form");
  const cancelBudgetBtn = document.getElementById("btn-cancel-budget-form");
  const setBudgetDrawer = document.getElementById("set-budget-drawer");

  const aiProposeBtn = document.getElementById("btn-ai-propose");
  const aiContainer = document.getElementById("ai-proposal-container");
  const aiLoading = document.getElementById("ai-loading-state");
  const aiError = document.getElementById("ai-error-state");
  const aiResult = document.getElementById("ai-result-state");

  const aiRecTotalEl = document.getElementById("ai-rec-total");
  const aiSummaryEl = document.getElementById("ai-summary-text");
  const aiCategoriesGrid = document.getElementById("ai-categories-grid");
  const aiItemsList = document.getElementById("ai-items-list");

  const applyBudgetOnlyBtn = document.getElementById("btn-apply-budget-only");
  const applyBothBtn = document.getElementById("btn-apply-budget-and-items");

  let latestProposal = null;

  function getCsrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str == null ? "" : String(str);
    return div.innerHTML;
  }

  if (toggleBudgetBtn && setBudgetDrawer) {
    toggleBudgetBtn.addEventListener("click", function () {
      setBudgetDrawer.classList.toggle("hidden");
    });
  }

  if (cancelBudgetBtn && setBudgetDrawer) {
    cancelBudgetBtn.addEventListener("click", function () {
      setBudgetDrawer.classList.add("hidden");
    });
  }

  function renderProposal(proposal) {
    latestProposal = proposal;
    aiRecTotalEl.textContent = `${proposal.currency || currency} ${proposal.recommended_total_budget}`;
    aiSummaryEl.textContent = proposal.summary || "";

    aiCategoriesGrid.innerHTML = (proposal.categories || [])
      .map(function (c) {
        return `
          <div class="rounded-xl border border-gray-200 bg-gray-50/70 p-3.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold uppercase tracking-wide text-gray-600">${escapeHtml(c.label)}</span>
              <span class="text-sm font-bold text-gray-900">${escapeHtml(proposal.currency || currency)} ${escapeHtml(c.estimated_amount)}</span>
            </div>
            ${c.rationale ? `<p class="mt-1 text-xs text-gray-500">${escapeHtml(c.rationale)}</p>` : ""}
          </div>
        `;
      })
      .join("");

    aiItemsList.innerHTML = (proposal.proposed_expenses || [])
      .map(function (item) {
        return `
          <div class="flex items-center justify-between gap-4 px-4 py-3 text-sm">
            <div>
              <p class="font-semibold text-gray-900">${escapeHtml(item.title)}</p>
              <p class="text-xs text-gray-500">
                <span class="font-medium text-indigo-700">${escapeHtml(item.category_label || item.category)}</span>
                ${item.notes ? ` &bull; ${escapeHtml(item.notes)}` : ""}
              </p>
            </div>
            <span class="whitespace-nowrap font-bold text-gray-900">${escapeHtml(proposal.currency || currency)} ${escapeHtml(item.amount)}</span>
          </div>
        `;
      })
      .join("");
  }

  if (aiProposeBtn) {
    aiProposeBtn.addEventListener("click", async function () {
      aiContainer.classList.remove("hidden");
      aiLoading.classList.remove("hidden");
      aiError.classList.add("hidden");
      aiResult.classList.add("hidden");
      aiProposeBtn.disabled = true;

      try {
        const resp = await fetch(proposeUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({}),
        });
        const data = await resp.json();
        if (!resp.ok) {
          throw new Error(data.detail || "Failed to generate AI budget proposal.");
        }
        renderProposal(data);
        aiLoading.classList.add("hidden");
        aiResult.classList.remove("hidden");
      } catch (err) {
        aiLoading.classList.add("hidden");
        aiError.textContent = err.message || "Unable to contact Gemini AI right now.";
        aiError.classList.remove("hidden");
      } finally {
        aiProposeBtn.disabled = false;
      }
    });
  }

  async function applyProposal(includeExpenses) {
    if (!latestProposal) return;
    applyBudgetOnlyBtn.disabled = true;
    applyBothBtn.disabled = true;

    try {
      const resp = await fetch(applyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
          apply_budget: true,
          apply_expenses: includeExpenses,
          replace_existing_ai: true,
          recommended_total_budget: latestProposal.recommended_total_budget,
          proposed_expenses: latestProposal.proposed_expenses,
        }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || "Could not apply AI proposal.");
      }
      window.location.reload();
    } catch (err) {
      aiError.textContent = err.message || "Error saving AI proposal.";
      aiError.classList.remove("hidden");
      applyBudgetOnlyBtn.disabled = false;
      applyBothBtn.disabled = false;
    }
  }

  if (applyBudgetOnlyBtn) {
    applyBudgetOnlyBtn.addEventListener("click", function () {
      applyProposal(false);
    });
  }

  if (applyBothBtn) {
    applyBothBtn.addEventListener("click", function () {
      applyProposal(true);
    });
  }
})();


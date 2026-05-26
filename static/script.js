document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  const button = form?.querySelector(".submit-button");
  const resolutionSlider = document.getElementById("resolution");
  const resolutionValue = document.getElementById("resolution-value");
  const resolutionLabels = {
    1: "Very compact",
    2: "Very fast",
    3: "Fast",
    4: "Full HD",
    5: "4K (only available for gen4 and smallcam)",
  };

  if (!form || !button) return;

  function updateResolutionLabel(value) {
    if (!resolutionValue) return;
    resolutionValue.textContent = resolutionLabels[value] || value;
  }

  if (resolutionSlider && resolutionValue) {
    updateResolutionLabel(resolutionSlider.value);
    resolutionSlider.addEventListener("input", function () {
      updateResolutionLabel(this.value);
    });
  }

  form.addEventListener("submit", function () {
    button.disabled = true;
    button.classList.add("loading");

    const text = button.querySelector(".button-text");
    if (text) {
      text.textContent = "Generating...";
    }
  });
});

const yearNode = document.getElementById("year");
if (yearNode) {
  yearNode.textContent = String(new Date().getFullYear());
}

const revealNodes = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window && revealNodes.length > 0) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  revealNodes.forEach((node) => observer.observe(node));
} else {
  revealNodes.forEach((node) => node.classList.add("is-visible"));
}

const contactForm = document.getElementById("contact-form");
if (contactForm) {
  const submitButton = contactForm.querySelector('button[type="submit"]');
  const statusNode = document.getElementById("contact-form-status");
  const defaultButtonText = submitButton ? submitButton.textContent : "Send Inquiry";

  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!contactForm.reportValidity()) {
      return;
    }

    const action = contactForm.getAttribute("action") || "";
    const endpoint = action.includes("formsubmit.co/ajax/")
      ? action
      : action.replace("formsubmit.co/", "formsubmit.co/ajax/");

    if (!endpoint.includes("formsubmit.co")) {
      contactForm.submit();
      return;
    }

    const formData = new FormData(contactForm);

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.textContent = "Sending...";
    }

    if (statusNode) {
      statusNode.textContent = "";
      statusNode.classList.remove("is-success", "is-error");
    }

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Submit failed");
      }

      contactForm.reset();

      if (statusNode) {
        statusNode.textContent = "Success. Your form was sent. I will get back to you soon.";
        statusNode.classList.add("is-success");
      }
    } catch (error) {
      if (statusNode) {
        statusNode.textContent =
          "Could not send right now. Please try again or email me directly.";
        statusNode.classList.add("is-error");
      }
    } finally {
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.textContent = defaultButtonText;
      }
    }
  });
}

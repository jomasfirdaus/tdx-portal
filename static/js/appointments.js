// Appointment booking page — Service Area / Date -> availability lookup ->
// Slot picker. Vanilla JS, no dependencies (keeps the CSP's script-src
// 'self' intact). The <select id="id_slot"> element itself is the single
// source of truth submitted with the form; this script only rebuilds its
// <option> list from the appointments:availability JSON endpoint. If JS is
// disabled, the select still works with the full slot list rendered
// server-side (AppointmentForm's default queryset) — degraded but valid.
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("appointment-form");
    if (!form) return;

    var serviceAreaField = document.getElementById("id_service_area");
    var dateField = document.getElementById("id_appointment_date");
    var slotField = document.getElementById("id_slot");
    var hint = document.getElementById("slot-hint");
    if (!serviceAreaField || !dateField || !slotField || !hint) return;

    var availabilityUrl = form.getAttribute("data-availability-url");
    var textSelect = form.getAttribute("data-hint-select");
    var textLoading = form.getAttribute("data-hint-loading");
    var textEmpty = form.getAttribute("data-hint-empty");
    var textError = form.getAttribute("data-hint-error");
    var spotsLeftTemplate = form.getAttribute("data-spots-left-template") || "{n}";

    // Track the in-flight request so a fast second change (e.g. typing a
    // date) can't have its response overwritten by a slower, older one.
    var requestToken = 0;

    function clearSlotOptions() {
      slotField.innerHTML = "";
    }

    function setHint(text) {
      hint.textContent = text;
    }

    function addPlaceholderOption(text) {
      var option = document.createElement("option");
      option.value = "";
      option.textContent = text;
      option.disabled = true;
      option.selected = true;
      slotField.appendChild(option);
    }

    function formatSpotsLeft(remaining) {
      return spotsLeftTemplate.replace("{n}", remaining);
    }

    function populateSlots(slots, previousValue) {
      clearSlotOptions();
      if (!slots.length) {
        slotField.disabled = true;
        addPlaceholderOption(textEmpty);
        setHint(textEmpty);
        return;
      }
      slotField.disabled = false;
      slots.forEach(function (slot) {
        var option = document.createElement("option");
        option.value = slot.id;
        option.textContent = slot.start_time + "\u2013" + slot.end_time + " \u00b7 " + formatSpotsLeft(slot.remaining);
        slotField.appendChild(option);
      });
      if (previousValue && slots.some(function (slot) { return String(slot.id) === String(previousValue); })) {
        slotField.value = previousValue;
      }
      setHint("");
    }

    function fetchAvailability() {
      var serviceAreaId = serviceAreaField.value;
      var date = dateField.value;
      var previousValue = slotField.value;

      clearSlotOptions();
      slotField.disabled = true;

      if (!serviceAreaId || !date) {
        addPlaceholderOption(textSelect);
        setHint(textSelect);
        return;
      }

      setHint(textLoading);
      addPlaceholderOption(textLoading);

      var currentToken = ++requestToken;
      var url = availabilityUrl + "?service_area=" + encodeURIComponent(serviceAreaId) + "&date=" + encodeURIComponent(date);

      fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (response) {
          return response.json()
            .catch(function () { return null; })
            .then(function (data) { return { ok: response.ok, data: data }; });
        })
        .then(function (result) {
          if (currentToken !== requestToken) return; // a newer request has already superseded this one
          if (!result.ok) {
            var message = (result.data && result.data.message) || textError;
            clearSlotOptions();
            slotField.disabled = true;
            addPlaceholderOption(message);
            setHint(message);
            return;
          }
          populateSlots((result.data && result.data.slots) || [], previousValue);
        })
        .catch(function () {
          if (currentToken !== requestToken) return;
          clearSlotOptions();
          slotField.disabled = true;
          addPlaceholderOption(textError);
          setHint(textError);
        });
    }

    serviceAreaField.addEventListener("change", fetchAvailability);
    dateField.addEventListener("change", fetchAvailability);

    // On initial load the picker is empty until both fields are chosen —
    // matches the "pick a service and date first" flow. If the form was
    // re-rendered after a validation error with a service_area/date already
    // filled in (e.g. only the name failed validation), re-fetch so the
    // previously-chosen slot list comes back instead of sitting empty.
    if (serviceAreaField.value && dateField.value) {
      fetchAvailability();
    } else {
      clearSlotOptions();
      addPlaceholderOption(textSelect);
      slotField.disabled = true;
    }
  });
})();

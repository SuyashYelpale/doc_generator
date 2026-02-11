document.addEventListener("DOMContentLoaded", function () {

    /* ================= SALARY BREAKDOWN ================= */

    const btn = document.getElementById("salary_breakdown_btn");
    const card = document.getElementById("salary_breakdown_card");
    const ctcInput = document.getElementById("ctc");

    if (btn && card && ctcInput) {

        btn.addEventListener("click", function () {

            const ctc = parseFloat(ctcInput.value);

            if (!ctc || isNaN(ctc)) {
                alert("Please enter valid CTC");
                return;
            }

            const basicAnnual = ctc * 0.40;
            const hraAnnual = basicAnnual * 0.20;
            const pfAnnual = basicAnnual * 0.12;
            const gratuityAnnual = basicAnnual * 0.0481;
            const specialAnnual =
                ctc - (basicAnnual + hraAnnual + pfAnnual + gratuityAnnual);

            function format(num) {
                return num.toLocaleString("en-IN", {
                    maximumFractionDigits: 0
                });
            }

            const setValue = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.innerText = format(value);
            };

            setValue("basic_annual", basicAnnual);
            setValue("basic_monthly", basicAnnual / 12);

            setValue("hra_annual", hraAnnual);
            setValue("hra_monthly", hraAnnual / 12);

            setValue("pf_annual", pfAnnual);
            setValue("pf_monthly", pfAnnual / 12);

            setValue("gratuity_annual", gratuityAnnual);
            setValue("gratuity_monthly", gratuityAnnual / 12);

            setValue("special_annual", specialAnnual);
            setValue("special_monthly", specialAnnual / 12);

            // Toggle card safely
            if (card.style.display === "none" || card.style.display === "") {
                card.style.display = "block";
                btn.textContent = "Hide Salary Breakdown";
            } else {
                card.style.display = "none";
                btn.textContent = "Show Salary Breakdown";
            }

        });
    }

    /* ================= AUTO FILL ACCOUNT HOLDER ================= */

    const fullName = document.getElementById("full_name");
    const accountHolder = document.getElementById("account_holder");

    if (fullName && accountHolder) {
        fullName.addEventListener("blur", function () {
            if (!accountHolder.value) {
                accountHolder.value = this.value;
            }
        });
    }

    /* ================= EMPLOYEE ID GENERATION ================= */

    function generateEmployeeId() {

        const fullNameField = document.getElementById("full_name");
        const employeeIdField = document.getElementById("employee_id");

        if (!fullNameField || !employeeIdField) return;

        const fullName = fullNameField.value.trim();
        if (!fullName) return;

        const nameParts = fullName.split(" ");
        let idPrefix = "";

        if (nameParts.length >= 3) {
            idPrefix =
                nameParts[0][0].toUpperCase() +
                nameParts[1].toUpperCase() +
                nameParts[nameParts.length - 1][0].toUpperCase();
        } else if (nameParts.length === 2) {
            idPrefix =
                nameParts[0][0].toUpperCase() +
                nameParts[1][0].toUpperCase();
        } else {
            idPrefix = nameParts[0][0].toUpperCase();
        }

        const randomNum = Math.floor(1001 + Math.random() * 8999);
        employeeIdField.value = idPrefix + randomNum;
    }

    const fullNameField = document.getElementById("full_name");
    const employeeIdField = document.getElementById("employee_id");

    if (fullNameField && employeeIdField) {

        fullNameField.addEventListener("blur", function () {
            if (!employeeIdField.value) {
                generateEmployeeId();
            }
        });

        if (fullNameField.value && !employeeIdField.value) {
            generateEmployeeId();
        }
    }

    const generateIdBtn = document.getElementById("generate_id_btn");
    if (generateIdBtn) {
        generateIdBtn.addEventListener("click", generateEmployeeId);
    }

    /* ================= MONTH YEAR PRINT ================= */

    function updatePrintText() {

        const monthField = document.getElementById("month");
        const yearField = document.getElementById("year");
        const outputField = document.getElementById("printMonthYear");

        if (monthField && yearField && outputField) {
            outputField.textContent =
                monthField.value + " " + yearField.value;
        }
    }

    const monthEl = document.getElementById("month");
    const yearEl = document.getElementById("year");

    if (monthEl) monthEl.addEventListener("change", updatePrintText);
    if (yearEl) yearEl.addEventListener("input", updatePrintText);

});

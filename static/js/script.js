document.addEventListener('DOMContentLoaded', function() {
    // Show/hide resignation date based on document type
    const documentType = document.getElementById('document_type');
    const resignationDateContainer = document.getElementById('resignation_date_container');
    
    documentType.addEventListener('change', function() {
        if (this.value === 'experience_letter' || this.value === 'relieving_letter') {
            resignationDateContainer.style.display = 'block';
            document.getElementById('resignation_date').required = true;
        } else {
            resignationDateContainer.style.display = 'none';
            document.getElementById('resignation_date').required = false;
        }
    });
    
    // Salary breakdown toggle
    const salaryBreakdownBtn = document.getElementById('salary_breakdown_btn');
    const salaryBreakdownCard = document.getElementById('salary_breakdown_card');
    
    salaryBreakdownBtn.addEventListener('click', function() {
        if (salaryBreakdownCard.style.display === 'none') {
            salaryBreakdownCard.style.display = 'block';
            this.textContent = 'Hide Salary Breakdown';
            
            // Auto-calculate salary breakdown if CTC is provided
            const ctc = parseFloat(document.getElementById('ctc').value);
            if (ctc && !isNaN(ctc)) {
                const monthly = ctc / 12;
                document.getElementById('basic').value = (monthly * 0.4).toFixed(2); // 40% basic
                document.getElementById('hra').value = (monthly * 0.2).toFixed(2);   // 20% HRA
                document.getElementById('da').value = (monthly * 0.1).toFixed(2);    // 10% DA
                document.getElementById('conveyance').value = (monthly * 0.05).toFixed(2);
                document.getElementById('medical').value = (monthly * 0.05).toFixed(2);
                document.getElementById('special_allowance').value = (monthly * 0.2).toFixed(2);
                document.getElementById('pf').value = (monthly * 0.12).toFixed(2);   // 12% of basic
                document.getElementById('professional_tax').value = (200).toFixed(2); // Fixed PT
            }
        } else {
            salaryBreakdownCard.style.display = 'none';
            this.textContent = 'Show Salary Breakdown';
        }
    });
    
    // Auto-fill account holder name if empty
    const fullName = document.getElementById('full_name');
    const accountHolder = document.getElementById('account_holder');
    
    fullName.addEventListener('blur', function() {
        if (!accountHolder.value) {
            accountHolder.value = this.value;
        }
    });

    // Employee ID Generation
    function generateEmployeeId() {
        const fullName = document.getElementById('full_name').value.trim();
        if (!fullName) return;
        
        const nameParts = fullName.split(' ');
        let idPrefix = '';
        
        if (nameParts.length >= 3) {
            // First letter of first name + middle name + first letter of last name
            idPrefix = nameParts[0][0].toUpperCase() + 
                      nameParts[1].toUpperCase() + 
                      nameParts[nameParts.length-1][0].toUpperCase();
        } else if (nameParts.length === 2) {
            // First letter of first name + first letter of last name
            idPrefix = nameParts[0][0].toUpperCase() + 
                      nameParts[1][0].toUpperCase();
        } else {
            // Just first letter if only one name
            idPrefix = nameParts[0][0].toUpperCase();
        }
        
        // Generate a random 4-digit number (1001-9999)
        const randomNum = Math.floor(1001 + Math.random() * 8999);
        const employeeId = idPrefix + randomNum;
        
        document.getElementById('employee_id').value = employeeId;
    }

    // Set up event listeners for employee ID generation
    const employeeIdField = document.getElementById('employee_id');
    const fullNameField = document.getElementById('full_name');
    
    // Generate when name changes
    fullNameField.addEventListener('blur', function() {
        if (!employeeIdField.value) {
            generateEmployeeId();
        }
    });
    
    // Add generate button functionality if exists
    const generateIdBtn = document.getElementById('generate_id_btn');
    if (generateIdBtn) {
        generateIdBtn.addEventListener('click', generateEmployeeId);
    }
    
    // Generate on page load if name exists
    if (fullNameField.value && !employeeIdField.value) {
        generateEmployeeId();
    }

    // ----------------- Month/Year Print Update -----------------
    function updatePrintText() {
        const monthField = document.getElementById("month");
        const yearField = document.getElementById("year");
        const outputField = document.getElementById("printMonthYear");

        if (monthField && yearField && outputField) {
            const month = monthField.value;
            const year = yearField.value;
            outputField.textContent = month + " " + year;
        }
    }

    // Attach event listeners if elements exist
    const monthEl = document.getElementById("month");
    const yearEl = document.getElementById("year");
    if (monthEl && yearEl) {
        monthEl.addEventListener("change", updatePrintText);
        yearEl.addEventListener("input", updatePrintText);
    }
});

// Hide custom school input when something specific is selected.
var schoolElem = document.getElementById("id_school");
var altSchoolElems = document.querySelectorAll("#id_school_alt_name,#id_school_alt_street,#id_school_alt_zip_code,#id_school_alt_city");

function onSchoolSelectChanged() {
    if (this.value === "--jiná--") {
        altSchoolElems.forEach(function (elem) {
            elem.closest(".column").classList.remove("is-hidden");
        });
    } else {
        altSchoolElems.forEach(function (elem) {
            elem.closest(".column").classList.add("is-hidden");
        });
    }
}

schoolElem.addEventListener("change", onSchoolSelectChanged);
onSchoolSelectChanged.call(schoolElem);

/* Tag inline code that is exactly an mzTab-M section prefix (MTD, SML/SMH,
   SMF/SFH, SME/SEH) so the "sections" theme variant can color it. */
(function () {
  var map = { MTD: 'mtd', SML: 'sml', SMH: 'sml', SMF: 'smf', SFH: 'smf', SME: 'sme', SEH: 'sme' }
  document.querySelectorAll('.doc :not(pre) > code').forEach(function (el) {
    var key = map[el.textContent.trim()]
    if (key) el.classList.add('mz-sec', 'mz-sec-' + key)
  })
})()

/* Backend page setup - moved out of inline <script> for CSP 'self' script-src. */
(function ($) {
    if (!$) { return; }
    $(function () {
        if ($.fn.customSelect) {
            $('select.styled').customSelect();
        }
        if ($.fn.datetimepicker) {
            $('#datetimepicker').datetimepicker({format: 'unixtime', inline: true});
        }
    });
})(window.jQuery);

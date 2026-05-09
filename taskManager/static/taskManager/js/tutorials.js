/* Tutorial page bootstrap glue. Moved out of inline <script> so CSP can
 * forbid script-src 'unsafe-inline' (CWE-79). */
(function ($) {
    if (typeof window.hljs !== 'undefined' &&
        typeof window.hljs.initHighlightingOnLoad === 'function') {
        window.hljs.initHighlightingOnLoad();
    }
    $(function () {
        if ($.fn.customSelect) {
            $('select.styled').customSelect();
        }
        $('#creds').hide();
        $('#show_creds').on('click', function (e) {
            e.preventDefault();
            $('#creds').show();
            $('#show_creds').hide();
        });
    });
})(window.jQuery);

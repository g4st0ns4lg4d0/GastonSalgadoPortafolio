document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.markdown-editor').forEach(editor => {
    const input = editor.querySelector('textarea');
    const toolbar = editor.querySelector('.markdown-toolbar');
    toolbar.hidden = false;
    toolbar.addEventListener('click', event => {
      const button = event.target.closest('button');
      if (!button) return;
      const selected = input.value.slice(input.selectionStart, input.selectionEnd) || 'texto';
      const formats = {strong: `**${selected}**`, em: `*${selected}*`, list: `\n- ${selected}\n`, heading: `\n### ${selected}\n`, link: `[${selected}](https://ejemplo.cl)`};
      input.setRangeText(formats[button.dataset.format], input.selectionStart, input.selectionEnd, 'select');
      input.dispatchEvent(new Event('input', {bubbles: true}));
      input.focus();
    });
  });
});

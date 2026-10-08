<template>
  <div class="editor-actions"><slot /></div>
</template>

<style>
.editor-actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  max-width: 100%;
}
.editor-actions > button {
  flex: 0 0 auto;
  white-space: nowrap;
}
.editor-actions > button:first-child:not(:only-child) {
  background: var(--primary-color, #03a9f4);
  color: var(--text-primary-color, #fff);
}
</style>

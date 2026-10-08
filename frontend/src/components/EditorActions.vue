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
</style>

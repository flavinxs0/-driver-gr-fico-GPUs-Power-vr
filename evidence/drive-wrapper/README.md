# Pacote wrapper do Google Drive

O arquivo compartilhado foi analisado, mas os ELF proprietários não são versionados neste repositório. O pacote contém o carregador Adrenotools e hooks; ele não contém `libvulkan_powervr_mesa.so`.

Arquivo analisado: `wrapper-powervr-arm64 (1).zip`

SHA-256: `1da73002f18a4256a48a661c8e7497d0768b74d77716c5c264f2808c8f952627`

O manifest ICD abaixo aponta para `libvulkan_wrapper.so`. Para o teste completo, o Mesa PVR nativo deve ser fornecido separadamente pelo mecanismo de driver customizado.

As dependências e o RUNPATH observados no pacote estão documentados em [`../drive-log-wrapper-analysis-2026-11-05.md`](../drive-log-wrapper-analysis-2026-11-05.md).

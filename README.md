# Mesa PVR — PowerVR BXM-8-256 / MT6855

Build experimental do driver Vulkan Mesa `vulkan_pvr` para PowerVR BXM-8-256, BVNC `35.3.408.101`, usando o módulo MT6855 enviado e sua ABI Rogue DDK `1.15@6133110`.

Este repositório contém os patches reproduzíveis, os testes offline de bridge e o workflow de build Android. Ele não contém APK e não modifica o kernel. O driver precisa ser usado somente em um ambiente compatível com o módulo PowerVR do dispositivo.

## Build

A compilação Android é executada pelo GitHub Actions em um runner x86_64 com Android NDK. O workflow prepara uma base Mesa fixa, aplica os seis patches, compila as ferramentas nativas do Mesa, compila `libvulkan_powervr_mesa.so` para `aarch64-linux-android` e gera somente o pacote principal Adrenotools em `dist/`.

O patch 0006 altera a negociação do cliente para DDK 1.15/build 6133110. Os patches 0002 e 0003 preservam código experimental de bridge B-Series, mas o caminho usado pelo MT6855 é o caminho genérico Mesa 1.x; o cabeçalho v25 não deve ser selecionado para esse módulo.

## Evidências reunidas

A análise conjunta dos pacotes PowerVR, Mesa PVR, DXVK, logs do Moto G56 e do wrapper Adrenotools está em [`evidence/unified-powervr-analysis-2026-11-05.md`](evidence/unified-powervr-analysis-2026-11-05.md). A análise específica do ZIP compartilhado no Google Drive está em [`evidence/drive-log-wrapper-analysis-2026-11-05.md`](evidence/drive-log-wrapper-analysis-2026-11-05.md).

O wrapper do Drive é apenas uma camada de loader/hook e não contém `libvulkan_powervr_mesa.so`. Binários proprietários MediaTek/PowerVR e o módulo de kernel não são versionados neste repositório; são usados somente como evidência estática para ABI e compatibilidade.

A análise dos dois logs recentes do Moto G73 está em [`evidence/dragonburst-moto-g73-2026-11-06.md`](evidence/dragonburst-moto-g73-2026-11-06.md). Ela separa o fallback do driver de sistema da falha de carregamento do wrapper e documenta por que a causa do crash Mesa ainda precisa ser capturada.

Para coletar propriedades, nodes gráficos, módulos, AVCs do kernel e logcat após reproduzir a falha, use `tools/collect_android_pvr_trace.sh` em um computador com Android platform-tools. O script não limpa os logs; revise e remova dados pessoais do `logcat.txt` antes de compartilhar.

## Estado

O build host e os testes offline foram aprovados. O build Android e o ZIP final só devem ser considerados prontos após uma execução verde do workflow e inspeção do artefato gerado.

A análise do módulo está em [`evidence/mt6855-analysis.md`](evidence/mt6855-analysis.md).

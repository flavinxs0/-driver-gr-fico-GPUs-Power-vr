# Handshake_DDK.zip — análise técnica

Data da análise: 2026-11-04

## Conteúdo

O arquivo contém sete bibliotecas Android:

- `libPVRMtkutils.so`
- `libdpframework.so`
- `libion_mtk.so`
- `libmpvr.so`
- `libufwriter.so`
- `libusc.so`
- `vendor.mediatek.hardware.mms@1.5.so`

O ZIP está íntegro e todas as bibliotecas são ELF **ARM 32-bit (EABI5)**. Portanto, elas não podem ser ligadas diretamente ao driver Mesa Android AArch64 que este repositório produz.

## O que o pacote confirma

`libusc.so` exporta símbolos do compilador proprietário UniFlex/USC, incluindo:

- `PVRUniFlexCreateContext`
- `PVRUniFlexCompileToHw`
- `PVRUniFlexCompileKernels`
- `PVRUniflexWriteHWBinary`
- `PVRUniFlexCreateRenderTargetSetup`

`libufwriter.so` depende de `libusc.so` e de `libsrv_um.so`. Isso confirma que o caminho proprietário usa um compilador Rogue/UniFlex e uma camada de serviços PowerVR, mas não fornece uma implementação aberta da ABI de comandos, memória, PMR ou bridge do kernel.

## Decisão de engenharia

As bibliotecas não serão incluídas nem linkadas no Mesa. Elas são blobs proprietários, são ARM32 e possuem dependências vendor ausentes no build AArch64. Usá-las diretamente criaria um driver híbrido, não um backend Mesa independente, além de impedir uma distribuição reproduzível.

O material é mantido como evidência para orientar o backend PCO/USC livre. A implementação Mesa deve continuar usando o compilador PCO/Rogue presente no código-fonte Mesa e a winsys `pvrsrvkm`, com a ABI correspondente ao módulo MT6855 identificado no projeto.

## Erro de CI relacionado

A execução `41938739868` falhou antes da compilação do driver porque o workflow configurava o build das ferramentas nativas com `-Dplatforms=x11`. O Mesa então exigia `xrandr.pc`, ausente no runner:

```text
research/mesa-src/meson.build:2382:22: ERROR: Dependency "xrandr" not found
```

Como essas ferramentas não precisam de X11, o workflow foi corrigido para usar `-Dplatforms=` e desabilitar EGL/GBM no build nativo. Isso elimina a dependência desnecessária sem alterar o driver Android.

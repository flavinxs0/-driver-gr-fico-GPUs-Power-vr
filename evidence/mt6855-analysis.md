# Análise offline — `pvrsrvkm_mt6855_sec.ko`

Data da análise: 2026-11-04.

## Identidade do módulo

- Arquivo: `pvrsrvkm_mt6855_sec.ko`
- Arquitetura: ELF64 relocável AArch64
- SHA-256: `991dfd526d2b0eebdea4857677e51c0ec978336e0a764719704aa03e51d58b98`
- Nome: `pvrsrvkm_mt6855_sec`
- Kernel vermagic: `5.10.240-android12-9-39412-gf523a0c1bb6f SMP preempt mod_unload modversions aarch64`
- SCM version: `g70224437a25b`
- Licença declarada: Dual MIT/GPL
- Dependências do módulo: `mtk_gpufreq_wrapper`, `mtk_gpu_hal`, `ged`, `mtk_tinysys_ipi`, `gpueb`
- Driver/stack informado no binário: `Rogue_DDK_Android rogueddk 1.15@6133110`

## GPU/BVNC

O módulo contém a string e a configuração `35.3.408.101`, além de rotinas de verificação BVNC. Isso confirma o BVNC usado pelos patches atuais para este módulo.

## Bridges observadas

O módulo exporta símbolos de inicialização e despacho de bridges, incluindo:

- `InitSRVCOREBridge`
- `InitMMBridge`
- `InitRGXCMPBridge`
- `InitRGXTA3DBridge`
- `InitSYNCBridge`
- `InitCMMBridge`
- `PVRSRV_BridgeDispatchKM`
- `PVRSRVBridgeConnect`
- `PVRSRVBridgeDisconnect`
- `PVRSRVBridgePMRUnrefPMR`
- `PVRSRVBridgePMRUnrefUnlockPMR`

As strings de bridge incluem `PMRUNREFPMR`, `PHYSMEMNEWRAMBACKEDPMR`, criação/destruição de contexto e heaps, além de `SRVCORE_CONNECT`.

A desmontagem de `InitSRVCOREBridge` e `InitMMBridge` confirmou `SRVCORE=1` e `MM=6`. No grupo MM, o módulo registra funções consecutivas de `0` a `39`, incluindo o mesmo layout usado pelo bridge genérico Mesa: contexto em `15/16`, criação/destruição de heap em `17/18`, map/unmap PMR em `19/20`, reserve/unreserve em `21/22`, map/unmap pages em `24/25` e consultas de heap em `30/32`. Os tamanhos de entrada/saída observados para essas entradas também correspondem ao caminho Mesa 1.x, enquanto não correspondem ao cabeçalho experimental v25 usado anteriormente.

## Bloqueio técnico

O pacote original dos patches foi escrito assumindo DDK 25.1. O módulo real do MT6855 informa DDK 1.15 (`rogueddk 1.15@6133110`). Assim:

1. BVNC `35.3.408.101` está confirmado.
2. A existência das operações PMR/Devmem está confirmada.
3. A ABI, os IDs, os tamanhos das estruturas e as assinaturas dos bridges DDK 25.1 **não estão confirmados** para este módulo.
4. O código DDK 25.1 não deve ser carregado no aparelho sem uma camada específica para DDK 1.15 ou uma demonstração estática de equivalência.
5. Nenhum módulo foi carregado, executado ou enviado ao dispositivo.

## Validação Mesa host

- Base Mesa: `0d94b3f397fb9cf8470bb5600ada8af79ff5361a`
- Commit dos patches: `7fc1491ad706c4f5f9552302a90f4786c8ff5cbd`
- Os cinco patches aplicaram limpos.
- Teste offline `test_bridge_v25_mock`: aprovado.
- Build host do `vulkan_pvr`: concluído em 645 etapas.
- Artefato host: `build-host/src/imagination/vulkan/libvulkan_powervr_mesa.so`
- SHA-256 do artefato host: `1e6ceca69a414a07dd8943862e4a7f58d1f8d46163ee732fe679676f2002d831`
- Arquitetura do artefato: AArch64 ELF shared object.

O artefato host é uma prova de compilação do código Mesa e não é um APK nem uma biblioteca Android pronta. A build Android correta permanece bloqueada até a adaptação/validação da ABI DDK 1.15 do módulo MT6855.

## Ajuste aplicado no cliente Mesa

Como o mapa de bridges do módulo coincide com o caminho genérico Mesa 1.x, o cabeçalho `pvr_srv_bridge.h` foi ajustado para anunciar a versão `1.15` e o build `6133110`, exatamente como a string `Rogue_DDK_Android rogueddk 1.15@6133110` encontrada no módulo. O caminho experimental `v25` permanece separado e só é selecionado quando o kernel reportar major 25; ele não será usado pelo MT6855 que reporta major 1.

Esse ajuste corrige a negociação de versão, mas não substitui um teste no aparelho. A validação Android ainda precisa usar uma biblioteca compilada com NDK/ABI Android e confirmar o `DRM_IOCTL_SRVKM_CMD` contra o kernel real.

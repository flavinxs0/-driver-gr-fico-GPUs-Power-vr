# Análise unificada PowerVR/Mesa/DXVK — 2026-11-05

## Pacotes analisados

- `powerVR.zip`: `vkjson.json`, `vulkan.mtk.so`, `libsrv_um.so`, relatório MT6855/BXM-8-256 e inventário vendor.
- `mesapvr.zip`: buildkits Mesa, patches, scripts, ICD JSON e wrapper arm64.
- `powervr.soarquivos.zip`: bibliotecas PowerVR/MediaTek e módulo `pvrsrvkm_mt6855_sec.ko`.
- `dxvk.zip`: DXVK para testes de Vulkan, swapchain e recursos D3D.
- `Download.zip`: log do Moto G56 e wrapper.
- ZIP do Google Drive: pacote completo de wrapper com `wrapper.tzst`.

Os binários proprietários e o módulo de kernel foram analisados como evidência, mas não foram adicionados ao repositório.

## Resultado do Moto G56

O log comprova que o mecanismo de driver customizado conseguiu carregar:

```text
.../driver/libvulkan_powervr_mesa.so
```

Mas o Renut encerra com:

```text
o driver nao tem dispositivo
```

O carregamento do `.so` funcionou, porém a enumeração retornou zero dispositivos físicos ou a inicialização do backend falhou antes de `vkEnumeratePhysicalDevices`.

## Descoberta do ZIP do Drive

O arquivo `wrapper-powervr-arm64 (1).zip` contém `libvulkan_wrapper.so` e `wrapper.tzst`. Dentro do `wrapper.tzst` há:

```text
usr/share/vulkan/icd.d/wrapper_icd.aarch64.json
usr/lib/libadrenotools.so
usr/lib/libmain_hook.so
usr/lib/libhook_impl.so
usr/lib/libgsl_alloc_hook.so
usr/lib/libfile_redirect_hook.so
usr/lib/libvulkan_wrapper.so
```

Ele **não contém `libvulkan_powervr_mesa.so`**. É uma camada de loader/hook, não o backend Mesa PVR. O manifest ICD aponta para `libvulkan_wrapper.so`.

O wrapper depende de `libadrenotools.so`, `libdrm.so`, bibliotecas XCB, bibliotecas Android e `libc++_shared.so`. O RUNPATH observado inclui `/data/data/com.termux/files/usr/lib`, que não deve ser presumido em um app Android comum.

## Causa provável

O driver Mesa ainda precisa completar o caminho:

```text
drmGetDevices2 → open(/dev/dri/renderD*) → drmGetVersion
→ pvr_srv_connection_create → pvr_srv_init_module
→ vkEnumeratePhysicalDevices
```

O log atual só comprova o hook/dlopen. Não comprova acesso ao render node, negociação da bridge ou criação do `VkPhysicalDevice`.

Há também uma divergência que deve ser eliminada: as evidências do MT6855 apontam para `BVNC 35.3.408.101` e DDK `1.15@6133110`, enquanto parte dos patches originais usa o caminho DDK 25.1. O caminho do MT6855 deve permanecer em DDK 1.15; o bridge v25 não deve ser selecionado nesse módulo.

## Componentes aproveitáveis

### Usar no projeto

- Patches Mesa `0001`–`0006`, com DDK 1.15 como caminho do MT6855.
- Scripts de build, cross-file e empacotamento.
- `vkjson.json` e dumps do aparelho para validação.
- O mecanismo de hook/redirecionamento Adrenotools como integração Android.
- O manifest ICD como referência para o pacote final.
- DXVK como teste posterior de compatibilidade Vulkan.

### Usar somente como referência

- `pvrsrvkm_mt6855_sec.ko` para IDs/ABI.
- `libsrv_um.so` e `vulkan.mtk.so` para sequência de conexão e símbolos.
- `gralloc.rogue.so`, `libion_mtk.so` e bibliotecas MediaTek para entender o ambiente vendor.

### Não incluir no driver final

- Módulo de kernel `.ko`.
- `vulkan.mtk.so`, `libsrv_um.so`, `libPVROCL.so`, GLES/EGL e gralloc proprietários.
- `libvulkan_wrapper.so` como substituto do Mesa nativo.
- Hooks e headers específicos de Adreno/KGSL sem adaptação para PowerVR.

## Próxima correção

Adicionar logs no Mesa antes/depois de `drmGetDevices2`, abertura do render node, `drmGetVersion`, `pvr_srv_connection_create`, `pvr_srv_init_module` e `vkEnumeratePhysicalDevices`. O próximo teste só deve ser considerado bem-sucedido quando aparecer pelo menos um `VkPhysicalDevice` BXM-8-256.

A análise detalhada do pacote do Drive está em [`drive-log-wrapper-analysis-2026-11-05.md`](drive-log-wrapper-analysis-2026-11-05.md).

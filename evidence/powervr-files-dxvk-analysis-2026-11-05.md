# Análise dos arquivos PowerVR + DXVK — 2026-11-05

## Pacotes

- `powervr.soarquivos.zip`
  - SHA-256: `e57ef1114023dd7c0113d2da271f60f64b6f853f5c985f4f6c5f84704a966b22`
  - 20 arquivos, aproximadamente 46.6 MB descompactados.
- `dxvk.zip`
  - SHA-256: `1af2ee9eef9d7752dcf59074c7b516f1c6793c1b230bcd34cd550800eb23fb0e`
  - DXVK 1.10.3, logs D3D9/D3D11/DXGI.

## O que pode ser usado diretamente no Mesa PVR

### 1. ABI e identificação do kernel

`pvrsrvkm_mt6855_sec.ko` é um módulo ELF relocável AArch64 para o MT6855. As strings confirmam:

- BVNC: `35.3.408.101`
- Rogue DDK: `1.15@6133110`
- Bridges `SRVCORE`, `MM`, `SYNC`, `RGXCMP`, `RGXTA3D` e outras.
- Mensagens de compatibilidade DDK/BVNC, úteis para comparar com o bridge Mesa.

Este é o arquivo mais importante para a ABI do Mesa, mas não deve ser carregado, substituído ou modificado pelo driver de usuário.

### 2. `libsrv_um.so`

É a biblioteca de suporte de usuário Rogue correspondente ao kernel. As strings e símbolos listam operações como `PVRSRVConnect`, `PVRSRVBridgeCall`, alocação DevMem, DMA-BUF, fences, sync objects e mapas de memória.

Uso recomendado: referência estática para nomes de operações, fluxo de conexão, erros e sequência de alocação. Não copiar para um pacote Mesa como substituição: ela depende de bibliotecas Android/vendor e da ABI proprietária do DDK.

### 3. `vulkan.mtk.so`

É o Vulkan proprietário real do dispositivo, AArch64, com dependências em `libsrv_um.so`, `libusc.so`, `libufwriter.so`, `libPVRMtkutils.so`, `libEGL.so`, `libgpu_aux.so`, `libged.so`, `libgpud.so` e outras.

Uso recomendado: referência de integração e comparação de carregamento. As strings mostram que ele usa diretamente símbolos PVRSRV como `PVRSRVConnect`, `PVRSRVDevMemX*`, `PVRSRVDmaBuf*`, fences e timelines. Não é um driver Mesa reutilizável e não deve ser redistribuído dentro do ZIP Mesa.

### 4. `vkjson.json`

É a melhor fonte para comparar o que o driver proprietário anuncia ao Vulkan. Confirma:

- dispositivo: `PowerVR BXM-8-256`
- driver: `1.15@6133110`
- conformance: `1.2.0.6`
- `maxBoundDescriptorSets = 4`
- `maxPushConstantsSize = 128`
- `maxSamplerAnisotropy = 16`
- `maxPerStageDescriptorUniformBuffers = 16`
- `maxMemoryAllocationSize = 0x40000000`
- `VK_EXT_descriptor_indexing` e `VK_KHR_buffer_device_address` aparecem na lista de extensões.

Importante: a presença da extensão não significa que o recurso esteja habilitado. O próprio `vkjson` mostra apenas os grupos básicos de features e não comprova `bufferDeviceAddress` ou descriptor indexing como features ativas.

### 5. `libusc.so`, `libIMGegl.so`, `libEGL_mtk.so`, `libPVRMtkutils.so`

Servem como evidência do stack proprietário e da separação entre compilador USC, EGL IMG e utilitários MediaTek. São úteis para entender dependências e nomes de símbolos, mas são componentes vendor fechados, fortemente acoplados ao Android/MTK e não substituem o código Mesa.

## O que não deve ser usado no Mesa PVR

- `libPVROCL.so`: runtime OpenCL, não é backend Vulkan.
- `gralloc.rogue.so`, `libgpu_aux.so`, `libged.so`, `libgralloc_extra.so`, `libion_mtk.so`: integração Android/MediaTek de memória e gralloc, com dependências vendor ausentes em um pacote Mesa genérico.
- `libEGL.so`, `libGLESv2_mtk.so`: stack OpenGL/EGL proprietário; não corrigem o backend Vulkan.
- `libdrm.so` do pacote: biblioteca vendor pré-compilada; o Mesa deve usar sua própria libdrm/headers compatíveis.
- `pvrsrvkm_mt6855_sec.ko`: módulo de kernel; não deve ser distribuído como parte do driver de usuário.

A análise ELF mostra que quase todas essas bibliotecas dependem de nomes como `libgpud.so`, `libcutils.so`, `libhidlbase.so`, `libhardware.so`, `libgralloctypes.so`, `vendor.mediatek.hardware.mms@1.5.so` e `libdmabufheap.so`. Isso confirma que um “pacote copiando todos os .so” não seria portátil nem seguro.

## O que o DXVK acrescentou

### D3D9/DXGI

O DXVK 1.10.3 conseguiu criar um dispositivo Vulkan com:

- `Wrapper(PowerVR BXM-8-256)`
- Driver `1.473.1398`
- Vulkan `1.3.170`
- Heap de aproximadamente 7612 MiB
- Três tipos de memória observados.

Também criou swapchains em modo `IMMEDIATE_KHR`, com três imagens, sem indicar falha de apresentação.

Features relevantes observadas pelo DXVK:

- `geometryShader = 1`
- `textureCompressionBC = 1`
- `vertexPipelineStoresAndAtomics = 1`
- `shaderWriteWithoutFormat = 1`
- `samplerAnisotropy = 0`
- `multiDrawIndirect = 0`
- `tessellationShader = 0`
- `VK_KHR_buffer_device_address` foi enumerada, mas `bufferDeviceAddress = 0`.
- `VK_KHR_timeline_semaphore` foi enumerada, mas `timelineSemaphore = 0`.

O teste D3D9 é útil: prova que o driver proprietário consegue inicializar Vulkan, criar swapchain e executar pelo menos o caminho D3D9 do DXVK. Ele também confirma que anunciar uma extensão não significa oferecer o feature.

### D3D11

O log D3D11 contém apenas:

```text
D3D11CoreCreateDevice: Probing D3D_FEATURE_LEVEL_10_0
D3D11CoreCreateDevice: Requested feature level not supported
```

Portanto, não é um crash do Vulkan. O teste falhou antes por falta do feature level D3D11 solicitado pelo DXVK/AIO test. Isso não prova que o Vulkan PVR não funciona.

## Correlação com o DragonBurst/Renut

Os logs do DragonBurst exigiam `bufferDeviceAddress`, descriptor indexing, 8192 texturas e 5 descriptor sets. Os arquivos agora mostram por que o driver proprietário foi rejeitado:

- DXVK confirma `bufferDeviceAddress = 0`.
- O dispositivo confirma `maxBoundDescriptorSets = 4`, enquanto o Renut exige 5.
- A enumeração de `VK_EXT_descriptor_indexing`/`VK_KHR_buffer_device_address` não basta; as features reais precisam estar habilitadas e funcionar.

O caminho correto no Mesa é implementar/reportar apenas o que o hardware e o backend suportam. Não se deve forçar esses bits para passar pela checagem do Renut.

## Plano recomendado

1. Usar `pvrsrvkm_mt6855_sec.ko`, `libsrv_um.so`, `vulkan.mtk.so` e `vkjson.json` somente como referência ABI/feature.
2. Criar um probe Vulkan pequeno para o Mesa que registre exatamente extensões, `VkPhysicalDeviceFeatures2`, limites, driverUUID e caminho do ICD.
3. Repetir o mesmo probe no Moto G73 e no Moto G56 quando o log chegar.
4. Comparar o Mesa com o driver proprietário campo a campo, especialmente bridge de conexão, DevMem, DMA-BUF, sync/fences, heaps e external memory.
5. Usar o DXVK D3D9 como teste de inicialização/swapchain, mas não como prova de que o Renut pode rodar.
6. Não copiar binários vendor para o release Mesa; publicar apenas código, patches, biblioteca Mesa compilada e manifests próprios quando o build Android passar.

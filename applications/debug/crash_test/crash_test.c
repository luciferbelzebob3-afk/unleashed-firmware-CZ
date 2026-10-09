#include <furi_hal.h>
#include <furi.h>

#include <gui/gui.h>
#include <gui/view_dispatcher.h>
#include <gui/modules/submenu.h>

#define TAG "PadTest"

typedef struct {
    Gui* gui;
    ViewDispatcher* view_dispatcher;
    Submenu* submenu;
} PadTest;

typedef enum {
    PadTestViewSubmenu,
} PadTestView;

typedef enum {
    PadTestSubmenuKontrola,
    PadTestSubmenuKontrolaMessage,
    PadTestSubmenuAssert,
    PadTestSubmenuAssertMessage,
    PadTestSubmenuPad,
    PadTestSubmenuZastavit,
    PadTestSubmenuHeapUnderflow,
    PadTestSubmenuHeapOverflow,
} PadTestSubmenu;

static void crash_test_corrupt_heap_underflow(void) {
    const size_t block_size = 1000;
    const size_t underflow_size = 123;
    uint8_t* block = malloc(block_size);

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstringop-overflow" // that's what we want!
    memset(block - underflow_size, 0xDD, underflow_size); // -V769
#pragma GCC diagnostic pop

    free(block); // should crash here (if compiled with DEBUG=1)

    // If we got here, the heap wasn't able to detect our corruption and crash
    furi_crash("Test selhal, mel nastat pad s chybou \"FreeRTOS Assert\"");
}

static void crash_test_corrupt_heap_overflow(void) {
    const size_t block_size = 1000;
    const size_t overflow_size = 123;
    uint8_t* block1 = malloc(block_size);
    uint8_t* block2 = malloc(block_size);
    memset(block2, 12, 34); // simulate use to avoid optimization // -V597 // -V1086

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstringop-overflow" // that's what we want!
    memset(block1 + block_size, 0xDD, overflow_size); // -V769 // -V512
#pragma GCC diagnostic pop

    uint8_t* block3 = malloc(block_size);
    memset(block3, 12, 34); // simulate use to avoid optimization // -V597 // -V1086

    free(block3); // should crash here (if compiled with DEBUG=1)
    free(block2);
    free(block1);

    // If we got here, the heap wasn't able to detect our corruption and crash
    furi_crash("Test selhal, mel nastat pad s chybou \"FreeRTOS Assert\"");
}

static void crash_test_submenu_callback(void* context, uint32_t index) {
    PadTest* instance = (PadTest*)context;
    UNUSED(instance);

    switch(index) {
    case PadTestSubmenuKontrola:
        furi_check(false);
        break;
    case PadTestSubmenuKontrolaMessage:
        furi_check(false, "Test padu: furi_check se zpravou");
        break;
    case PadTestSubmenuAssert:
        furi_assert(false);
        break;
    case PadTestSubmenuAssertMessage:
        furi_assert(false, "Test padu: furi_assert se zpravou");
        break;
    case PadTestSubmenuPad:
        furi_crash("Test padu: furi_crash");
        break;
    case PadTestSubmenuZastavit:
        furi_halt("Test padu: furi_halt");
        break;
    case PadTestSubmenuHeapUnderflow:
        crash_test_corrupt_heap_underflow();
        break;
    case PadTestSubmenuHeapOverflow:
        crash_test_corrupt_heap_overflow();
        break;
    default:
        furi_crash();
    }
}

static uint32_t crash_test_exit_callback(void* context) {
    UNUSED(context);
    return VIEW_NONE;
}

PadTest* crash_test_alloc(void) {
    PadTest* instance = malloc(sizeof(PadTest));

    View* view = NULL;

    instance->gui = furi_record_open(RECORD_GUI);
    instance->view_dispatcher = view_dispatcher_alloc();
    view_dispatcher_attach_to_gui(
        instance->view_dispatcher, instance->gui, ViewDispatcherTypeFullscreen);

    // Menu
    instance->submenu = submenu_alloc();
    view = submenu_get_view(instance->submenu);
    view_set_previous_callback(view, crash_test_exit_callback);
    view_dispatcher_add_view(instance->view_dispatcher, PadTestViewSubmenu, view);
    submenu_add_item(
        instance->submenu, "Kontrola", PadTestSubmenuKontrola, crash_test_submenu_callback, instance);
    submenu_add_item(
        instance->submenu,
        "Kontrola se zpravou",
        PadTestSubmenuKontrolaMessage,
        crash_test_submenu_callback,
        instance);
    submenu_add_item(
        instance->submenu, "Assert", PadTestSubmenuAssert, crash_test_submenu_callback, instance);
    submenu_add_item(
        instance->submenu,
        "Assert se zpravou",
        PadTestSubmenuAssertMessage,
        crash_test_submenu_callback,
        instance);
    submenu_add_item(
        instance->submenu, "Pad", PadTestSubmenuPad, crash_test_submenu_callback, instance);
    submenu_add_item(
        instance->submenu, "Zastavit", PadTestSubmenuZastavit, crash_test_submenu_callback, instance);
    submenu_add_item(
        instance->submenu,
        "Podteceni haldy",
        PadTestSubmenuHeapUnderflow,
        crash_test_submenu_callback,
        instance);
    submenu_add_item(
        instance->submenu,
        "Preteceni haldy",
        PadTestSubmenuHeapOverflow,
        crash_test_submenu_callback,
        instance);

    return instance;
}

void crash_test_free(PadTest* instance) {
    view_dispatcher_remove_view(instance->view_dispatcher, PadTestViewSubmenu);
    submenu_free(instance->submenu);

    view_dispatcher_free(instance->view_dispatcher);
    furi_record_close(RECORD_GUI);

    free(instance);
}

int32_t crash_test_run(PadTest* instance) {
    view_dispatcher_switch_to_view(instance->view_dispatcher, PadTestViewSubmenu);
    view_dispatcher_run(instance->view_dispatcher);
    return 0;
}

int32_t crash_test_app(void* p) {
    UNUSED(p);

    PadTest* instance = crash_test_alloc();

    int32_t ret = crash_test_run(instance);

    crash_test_free(instance);

    return ret;
}

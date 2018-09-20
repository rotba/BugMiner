import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class MainTest {

    Main m = new Main();
    @Test
    void foo() {
    }
    @Test
    void foo_2() {
        assertEquals(m.foo(), 0);
    }
    @Test
    void gooTest() {
        m.goo();
    }
}
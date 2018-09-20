import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class NaimTest {

    Naim m = new Naim();
    @Test
    void gooTest() {
        assertEquals(m.goo(),0, "hey brother");
    }
    @Test
    void foo() {
        assertEquals(m.goo(),0, "hey brother");
    }
    @Test
    void boo() {
        assertEquals(m.boo(),0, "hey brother");
    }
}
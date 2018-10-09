package p_1;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class AmitTest {

    Amit a = new Amit();
    @Test
    void hoo() {
    }
    @Test
    void fooTest() {
        assertEquals(0,a.foo());
    }

    @Test
    void RTerrorTest() {
        assertEquals(1,a.RTerror());
    }
    
    @Test
    void deltaPassedTest() {
        assertEquals(0,a.foo());
    }

    @Test
    void delta_3_Test() {
        assertEquals(0,a.goo());
    }


}
#pragma pattern_limit 99999999999
#pragma array_limit 9999999999999
import std.io;
struct header {
padding [176];
//u32 stringlength;
};

struct strings {
    if ($-parent.beginBlock >= parent.header.stringlength)
        break;
    char string[];
};

struct block1 {
padding [8];
u32 size;
padding [size];
};

struct block2 {
padding [8];
u32 blocksize;
padding [8];
u32 stringsize;
char string[stringsize];
padding[76];
float intensity;
padding [blocksize - (80 + stringsize)];
//u32 data;
};

enum lighttype : u32 {
    point,
    spot,
    directional,
    area,
    sun
};

enum lightmode : u32 {
    dynamic,
    static,
    analytic
};

struct xyz {
    float x;
    float y;
    float z;
};


struct color {
    float r;
    float g;
    float b;
}  [[static, color(std::format("{:02X}{:02X}{:02X}", u8(255*r), u8(255*g), u8(255*b)))]];
 
 
struct reference {
padding [8];
lighttype type;
color color;
padding[36];
u32 lighting_mode;
float distance_attenuation_start;
padding[36];
float data [4]; //cam fade start/end, spec power/intensity
float inner_cone_angle;
padding [332];
};

struct instance {
padding [36];
lightmode mode;
xyz origin;
xyz forward;
xyz up;
padding [20];
};


struct referencedata {
padding [144];
u32 referencecount;
padding[12];
reference reference[referencecount];
padding[4];
block2 block2 [referencecount]; 
padding [12];
instance instance[referencecount];
};

struct final {
header header;
u64 beginBlock = $;
//strings strings[while(true)];
block1 block1[12];
referencedata referencedata;
};

final final @ 0;